import Foundation
import MusicKit
import AppKit

@main
struct XlgPlayer {
    static func main() {
        let args = CommandLine.arguments
        guard args.count > 1 else {
            print("Usage: xlg-player <song-id>")
            return
        }

        let songId = args[1]
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
                let request = MusicCatalogResourceRequest<Song>(matching: \.id, equalTo: MusicItemID(songId))
                let response = try await request.response()
                guard let song = response.items.first else {
                    print("Song not found")
                    app.terminate(nil)
                    return
                }

                let player = ApplicationMusicPlayer.shared
                player.queue = [song]
                try await player.play()
                print("Playing: \(song.title)")

                // Keep app running for playback
                // App will run until terminated
            } catch {
                print("Error: \(error)")
                app.terminate(nil)
            }
        }

        app.run()
    }
}
