# Paper Tunes Telegram Bot

A self-hosted Telegram bot that converts music into printable QR-code sheets and reconstructs music from photographed/scanned QR-code sheets.

**No LoRa. No third-party cloud. No external server.** The bot and processing pipeline are designed to run locally on a Raspberry Pi.

## Status

🚧 Initial scaffold — audio codec integration and Telegram handlers are being implemented.

## Planned pipeline

```text
Music file -> audio codec -> binary payload -> chunking -> QR codes -> PNG/PDF
PNG/photo -> QR detection -> chunk validation -> reassembly -> audio decoder -> music file
```

## Design goals

- Telegram as the user interface
- Local processing and temporary storage
- QR chunks carry their own session ID, sequence number, total count and checksum
- Photos can arrive in arbitrary order
- Missing/corrupt chunks are reported clearly
- Printable PNG and PDF output
- Docker deployment on Raspberry Pi
- No LoRa component
- No external storage service

## Important

The audio representation will be based on the Paper Tunes concept, but the implementation in this repository is being written as a clean, modular project rather than copying the original application.

## License

TBD.
