// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "xlg-player",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(name: "xlg-player")
    ]
)
