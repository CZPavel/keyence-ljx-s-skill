# I/O signal reference

- **READY** (output): indicates whether TRG input can be accepted
- **TRG** (input): external trigger input
- **EXT** (input): pauses image capture
- **TEST** (input): cancels terminal output operations
- **RESET** (input): sets output terminals to normal state and resets trigger-wait state
- **BUSY** (output): indicates measurement processing or terminal-block command execution
- **RUN** (output): turns ON when system enters Run mode when startup mode is Run mode
- **CMD_READY** (output): indicates acceptance of terminal-block command inputs
- **ACK** (output): indicates successful terminal-block command execution
- **NACK** (output): indicates failed terminal-block command execution
- **STO** (output): data-strobe output for terminal result data
- **OUT_DATA[15:0]** (output): outputs judgment-result data
- **OR** (output): total judgment output in terminal data-output timing
- **PST** (input): handshake input for terminal data switching
- **ERROR** (output): error output is shown for encoder-trigger timing when trigger period is violated
