# Command reference

| Command | Family | Purpose | Request | Response | Status |
|---|---|---|---|---|---|
| BC | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| BS | LJ-X8000 | save latest input profile as the specified master profile | BS,h,nnn | BS | OFFICIAL_EXACT |
| CA | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| CD | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| CE | LJ-X8000 | clear error status | CE | CE | OFFICIAL_EXACT |
| CR | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| CTD | LJ-X8000 | set delay between trigger input and image capture | CTD,1,nnn | CTD | OFFICIAL_EXACT |
| CW | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| DLL | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| DR | LJ-X8000 | read upper or lower judgment limit for specified tool | DR,nnn,k,b | DR,mmm | OFFICIAL_EXACT |
| DW | LJ-X8000 | change upper or lower judgment limit for specified tool | DW,nnn,k,b,mmm | DW | OFFICIAL_EXACT |
| EXR | LJ-X8000 | read currently enabled execute condition number | EXR | EXR,n | OFFICIAL_EXACT |
| EXW | LJ-X8000 | change currently enabled execute condition number | EXW,n | EXW | OFFICIAL_EXACT |
| FTP | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| MRS | LJ-X8000 | request measured value reset | MRS,n | MRS,n,t,nnn,... | MRS | OFFICIAL_EXACT |
| OE | LJ-X8000 | enable or disable output | OE,n | OE | OFFICIAL_EXACT |
| OW | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| PFR | LJ-X8000 | obtain latest measured profile | PFR,h | PFR,n,pppp,pppp,pppp,... | OFFICIAL_EXACT |
| PFRF | LJ-X8000 | obtain latest measured profile with fast response | PFRF,h | PFRF,h,t | PFRF,h,s,m | PFRF,n,pppp,pppp,pppp,... | OFFICIAL_EXACT |
| PLC | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| PR | LJ-X8000 | read SD card and inspection program currently being read | PR | PR,d,nnn | OFFICIAL_EXACT |
| PW | LJ-X8000 | load specified inspection program from SD card | PW,d,nnn | PW | OFFICIAL_EXACT |
| R0 | LJ-X8000 | switch controller to Run mode | R0 | R0 | OFFICIAL_EXACT |
| RB | LJ-X8000 | save current program settings and reboot | RB | RB | OFFICIAL_EXACT |
| RM | LJ-X8000 | read Run/Setup controller mode | RM | RM,n | OFFICIAL_EXACT |
| RS | LJ-X8000 | reset controller data and buffers | RS | RS | OFFICIAL_EXACT |
| S0 | LJ-X8000 | switch controller to Setup mode | S0 | S0 | OFFICIAL_EXACT |
| SS | LJ-X8000 | save current program and global settings | SS | SS | OFFICIAL_EXACT |
| STR | LJ-X8000 | read externally specified string | STR,n | STR,ssss | OFFICIAL_EXACT |
| STW | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| T1 | LJ-X8000 | issue a trigger | T1 | T1 | OFFICIAL_EXACT |
| TCP | None |  |  |  | OFFICIAL_CONTEXTUAL |
| TE | LJ-X8000 | enable or disable trigger input | TE,n | TE | OFFICIAL_EXACT |
| TIM | LJ-X8000 | issue a TIMING request | TIM,m,n | TIM,m,n,t,nnn,... | TIM | OFFICIAL_EXACT |
| TS | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| TW | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| VW | LJ-X8000 |  |  |  | OFFICIAL_CONTEXTUAL |
| ZR | LJ-X8000 | perform auto zero ON or OFF request | ZR,m,n | ZR,m,n,t,nnn,... | ZR | OFFICIAL_EXACT |
