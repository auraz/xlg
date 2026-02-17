import Foundation
import MusicKit
import AppKit

let socketPath = "/tmp/xlg-player.sock"

@main
struct XlgPlayer {
    @MainActor static var socketSource: DispatchSourceRead?
    @MainActor static var clientSources: [Int32: DispatchSourceRead] = [:]
    nonisolated(unsafe) static var player = ApplicationMusicPlayer.shared

    static func main() {
        let args = CommandLine.arguments
        guard args.count > 1 else {
            print("Usage: xlg-player [--playlist] <id> [id2 ...]")
            return
        }

        let isPlaylist = args[1] == "--playlist"
        let ids = isPlaylist ? Array(args.dropFirst(2)) : Array(args.dropFirst(1))
        guard !ids.isEmpty else {
            print("No IDs provided")
            return
        }

        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)

        Task { @MainActor in
            var status = MusicAuthorization.currentStatus
            if status != .authorized { status = await MusicAuthorization.request() }
            guard status == .authorized else {
                print("Not authorized")
                app.terminate(nil)
                return
            }
            await playContent(isPlaylist: isPlaylist, ids: ids)
            startSocketServer()
        }

        app.run()
    }

    @MainActor static func playContent(isPlaylist: Bool, ids: [String]) async {
        if isPlaylist {
            player.pause() // Stop MusicKit
            player.queue = ApplicationMusicPlayer.Queue(for: [] as [Song])
            let urlStr = "music://music.apple.com/us/playlist/\(ids[0])"
            if let url = URL(string: urlStr) {
                NSWorkspace.shared.open(url)
                try? await Task.sleep(nanoseconds: 500_000_000)
                runAppleScript("tell application \"Music\" to play")
            }
        } else {
            player.pause() // Stop MusicKit
            player.queue = ApplicationMusicPlayer.Queue(for: [] as [Song])
            let urlStr = "music://music.apple.com/us/song/\(ids[0])"
            if let url = URL(string: urlStr) {
                NSWorkspace.shared.open(url)
                try? await Task.sleep(nanoseconds: 1_000_000_000) // 1s delay
                runAppleScript("tell application \"Music\" to play")
            }
        }
    }

    @MainActor static func startSocketServer() {
        unlink(socketPath)
        let fd = socket(AF_UNIX, SOCK_STREAM, 0)
        guard fd >= 0 else {
            print("Failed to create socket")
            return
        }

        var addr = sockaddr_un()
        addr.sun_family = sa_family_t(AF_UNIX)
        withUnsafeMutablePointer(to: &addr.sun_path) { ptr in
            socketPath.withCString { src in
                _ = strcpy(UnsafeMutableRawPointer(ptr).assumingMemoryBound(to: CChar.self), src)
            }
        }

        let bindResult = withUnsafePointer(to: &addr) { ptr in
            ptr.withMemoryRebound(to: sockaddr.self, capacity: 1) { bind(fd, $0, socklen_t(MemoryLayout<sockaddr_un>.size)) }
        }
        guard bindResult == 0 else {
            print("Failed to bind socket")
            close(fd)
            return
        }
        listen(fd, 5)

        socketSource = DispatchSource.makeReadSource(fileDescriptor: fd, queue: .main)
        socketSource?.setEventHandler { acceptClient(serverFd: fd) }
        socketSource?.setCancelHandler { close(fd); unlink(socketPath) }
        socketSource?.resume()
        print("Socket server listening on \(socketPath)")
    }

    @MainActor static func acceptClient(serverFd: Int32) {
        let clientFd = accept(serverFd, nil, nil)
        guard clientFd >= 0 else { return }

        let source = DispatchSource.makeReadSource(fileDescriptor: clientFd, queue: .main)
        source.setEventHandler { handleClientData(clientFd: clientFd) }
        source.setCancelHandler {
            close(clientFd)
            clientSources.removeValue(forKey: clientFd)
        }
        clientSources[clientFd] = source
        source.resume()
    }

    @MainActor static func handleClientData(clientFd: Int32) {
        var buffer = [UInt8](repeating: 0, count: 1024)
        let bytesRead = read(clientFd, &buffer, buffer.count)
        guard bytesRead > 0 else {
            clientSources[clientFd]?.cancel()
            return
        }

        let message = String(bytes: buffer.prefix(bytesRead), encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let parts = message.components(separatedBy: " ")
        guard !parts.isEmpty else { return }

        Task { @MainActor in
            let response = await handleCommand(parts: parts)
            _ = response.withCString { write(clientFd, $0, strlen($0)) }
        }
    }

    @MainActor static func handleCommand(parts: [String]) async -> String {
        let cmd = parts[0].lowercased()
        let usingMusicKit = player.state.playbackStatus == .playing || player.state.playbackStatus == .paused
        switch cmd {
        case "pause":
            if usingMusicKit { player.pause() } else { runAppleScript("tell application \"Music\" to pause") }
            return "OK\n"
        case "resume", "play":
            if usingMusicKit { try? await player.play() } else { runAppleScript("tell application \"Music\" to play") }
            return "OK\n"
        case "toggle":
            if usingMusicKit {
                if player.state.playbackStatus == .playing { player.pause() } else { try? await player.play() }
            } else { runAppleScript("tell application \"Music\" to playpause") }
            return "OK\n"
        case "skip", "next":
            if usingMusicKit { try? await player.skipToNextEntry() } else { runAppleScript("tell application \"Music\" to next track") }
            return "OK\n"
        case "previous", "prev":
            if usingMusicKit { try? await player.skipToPreviousEntry() } else { runAppleScript("tell application \"Music\" to previous track") }
            return "OK\n"
        case "favorite", "love":
            runAppleScript("tell application \"Music\"\nset f to favorited of current track\nset favorited of current track to not f\nend tell")
            return "OK\n"
        case "volume":
            if parts.count > 1 {
                let arg = parts[1]
                setSystemVolume(arg)
            }
            return "OK\n"
        case "status":
            return getStatusJson() + "\n"
        case "--playlist":
            let ids = Array(parts.dropFirst())
            await playContent(isPlaylist: true, ids: ids)
            return "OK\n"
        default:
            await playContent(isPlaylist: false, ids: parts)
            return "OK\n"
        }
    }

    static func runAppleScript(_ script: String) {
        guard let appleScript = NSAppleScript(source: script) else { return }
        var error: NSDictionary?
        appleScript.executeAndReturnError(&error)
    }

    @MainActor static func getStatusJson() -> String {
        let volume = getSystemVolume()
        var isPlaying = false
        var title = ""
        var artist = ""

        // Check MusicKit player first (playing or paused with content)
        let mkStatus = player.state.playbackStatus
        if mkStatus == .playing || mkStatus == .paused {
            if let entry = player.queue.currentEntry, case .song(let song) = entry.item {
                isPlaying = mkStatus == .playing
                title = song.title
                artist = song.artistName
            }
        }

        // Fall back to Music.app if MusicKit has no content
        if title.isEmpty {
            if let script = NSAppleScript(source: "tell application \"Music\" to return player state as string") {
                var error: NSDictionary?
                let result = script.executeAndReturnError(&error)
                if error == nil, result.stringValue == "playing" { isPlaying = true }
            }
            if let script = NSAppleScript(source: "tell application \"Music\" to get {name of current track, artist of current track}") {
                var error: NSDictionary?
                let result = script.executeAndReturnError(&error)
                if error == nil, let list = result.coerce(toDescriptorType: typeAEList) {
                    if let t = list.atIndex(1) { title = t.stringValue ?? "" }
                    if let a = list.atIndex(2) { artist = a.stringValue ?? "" }
                }
            }
        }

        let escaped = { (s: String) -> String in
            s.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
        }
        return "{\"playing\":\(isPlaying),\"title\":\"\(escaped(title))\",\"artist\":\"\(escaped(artist))\",\"volume\":\(volume)}"
    }

    static func getSystemVolume() -> Int {
        let script = "output volume of (get volume settings)"
        guard let appleScript = NSAppleScript(source: script) else { return 50 }
        var error: NSDictionary?
        let result = appleScript.executeAndReturnError(&error)
        return result.int32Value > 0 ? Int(result.int32Value) : 50
    }

    static func setSystemVolume(_ arg: String) {
        var script: String
        if arg.hasPrefix("+") {
            let delta = Int(arg.dropFirst()) ?? 10
            script = "set volume output volume ((output volume of (get volume settings)) + \(delta))"
        } else if arg.hasPrefix("-") {
            let delta = Int(arg.dropFirst()) ?? 10
            script = "set volume output volume ((output volume of (get volume settings)) - \(delta))"
        } else if let val = Int(arg) {
            script = "set volume output volume \(min(100, max(0, val)))"
        } else {
            return
        }
        guard let appleScript = NSAppleScript(source: script) else { return }
        var error: NSDictionary?
        appleScript.executeAndReturnError(&error)
    }
}
