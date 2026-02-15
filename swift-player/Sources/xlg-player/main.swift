import Foundation
import MusicKit
import AppKit

@main
struct XlgPlayer {
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
            if status != .authorized {
                status = await MusicAuthorization.request()
            }

            guard status == .authorized else {
                print("Not authorized")
                app.terminate(nil)
                return
            }

            do {
                let player = ApplicationMusicPlayer.shared

                if isPlaylist {
                    let request = MusicCatalogResourceRequest<Playlist>(matching: \.id, equalTo: MusicItemID(ids[0]))
                    let response = try await request.response()
                    guard let playlist = response.items.first else {
                        print("Playlist not found")
                        app.terminate(nil)
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
                        if let song = response.items.first {
                            songs.append(song)
                        }
                    }
                    guard !songs.isEmpty else {
                        print("No songs found")
                        app.terminate(nil)
                        return
                    }
                    player.queue = ApplicationMusicPlayer.Queue(for: songs)
                    try await player.play()
                    print("Playing: \(songs.map { $0.title }.joined(separator: ", "))")
                }
            } catch {
                print("Error: \(error)")
                app.terminate(nil)
            }
        }

        app.run()
    }
}
