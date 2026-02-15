import Foundation
import MusicKit
import AppKit

let socketPath = "/tmp/xlg-player.sock"

@main
struct XlgPlayer {
    @MainActor static var socketSource: DispatchSourceRead?
    @MainActor static var clientSources: [Int32: DispatchSourceRead] = [:]

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

    static func playContent(isPlaylist: Bool, ids: [String]) async {
        do {
            let player = ApplicationMusicPlayer.shared
            if isPlaylist {
                let request = MusicCatalogResourceRequest<Playlist>(matching: \.id, equalTo: MusicItemID(ids[0]))
                let response = try await request.response()
                guard let playlist = response.items.first else {
                    print("Playlist not found")
                    return
                }
                player.queue = [playlist]
                try await player.play()
                print("Playing playlist: \(playlist.name)")
            } else {
                var songs: [Song] = []
                for id in ids {
                    let request = MusicCatalogResourceRequest<Song>(matching: \.id, equalTo: MusicItemID(id))
                    let response = try await request.response()
                    if let song = response.items.first { songs.append(song) }
                }
                guard !songs.isEmpty else {
                    print("No songs found")
                    return
                }
                player.queue = ApplicationMusicPlayer.Queue(for: songs)
                try await player.play()
                print("Playing: \(songs.map { $0.title }.joined(separator: ", "))")
            }
        } catch {
            print("Error: \(error)")
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

        let isPlaylist = parts[0] == "--playlist"
        let ids = isPlaylist ? Array(parts.dropFirst()) : parts

        Task { @MainActor in
            await playContent(isPlaylist: isPlaylist, ids: ids)
            let response = "OK\n"
            _ = response.withCString { write(clientFd, $0, strlen($0)) }
        }
    }
}
