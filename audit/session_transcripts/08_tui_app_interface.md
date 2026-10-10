# Session Transcript: Textual TUI Interface

```text
[?1049h[?1000h[?1003h[?1015h[?1006h[?25l[?1004h[>25u[?2026$p[?2048$p[?2004h[?7l[?1000h[?1003h[?1015h[?1006h ⭘                          Azure DevOps SDLC Agent — Interactive Coding & SDLC Assistant                      14:27:46 
                               │                                                                                        
 SESSIONS                      │  │                                                                                     
                               │  │ Agent:                                                                              
                               │  │                                                                                     
                               │  │   👋 Welcome to the Azure DevOps SDLC Agent!                                        
                               │  │                                                                                     
                               │  │   You are in an active interactive coding session. Ask questions, inspect code,     
                               │  │   or use slash commands:                                                            
                               │  │                                                                                     
                               │  │   • /ado: Inspect or verify Azure DevOps connection                                 
                               │  │   • /ado setup <org> <project> [repo]: Update Azure DevOps settings                 
                               │  │   • /run <ticket_id> [--dry-run]: Run pipeline on a work item                       
                               │                                                                                        
                               │  ┌──────────────────────────────────────────────────────────────────────────────────┐  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  └──────────────────────────────────────────────────────────────────────────────────┘  
                               │                                                                                        
                               │  ────────────────────────────────────────────────────────────────────────────────────  
                               │                                                                                        
 ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔              │  ▊▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▎  
     Refresh                   │  ▊  Type a coding query or slash command (/help, /ado)...                           ▎  
 ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁              │  ▊▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▎  
                               │                                                                                        
                                                                                                                         ⭘                          Azure DevOps SDLC Agent — Interactive Coding & SDLC Assistant                      14:27:46 
                               │                                                                                        
 SESSIONS                      │  │                                                                                     
                               │  │ Agent:                                                                              
                               │  │                                                                                     
                               │  │   👋 Welcome to the Azure DevOps SDLC Agent!                                        
                               │  │                                                                                     
                               │  │   You are in an active interactive coding session. Ask questions, inspect           
                               │  │   code, or use slash commands:                                                  ▅▅  
                               │  │                                                                                     
                               │  │   • /ado: Inspect or verify Azure DevOps connection                                 
                               │  │   • /ado setup <org> <project> [repo]: Update Azure DevOps settings                 
                               │  │   • /run <ticket_id> [--dry-run]: Run pipeline on a work item                       
                               │                                                                                        
                               │  ┌──────────────────────────────────────────────────────────────────────────────────┐  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  └──────────────────────────────────────────────────────────────────────────────────┘  
                               │                                                                                        
                               │  ────────────────────────────────────────────────────────────────────────────────────  
                               │                                                                                        
 ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔              │  ▊▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▎  
     Refresh                   │  ▊  Type a coding query or slash command (/help, /ado)...                           ▎  
 ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁              │  ▊▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▎  
                               │                                                                                                            Azure DevOps SDLC Agent — Interactive Coding & SDLC Assistant                     SESSIONS
│                                                                                   
│ Agent:                                                                            
#0 running - Work Item #0   
│                                                                                   
                            
│   👋 Welcome to the Azure DevOps SDLC Agent!                                      
                            
│                                                                                   
                            
│   You are in an active interactive coding session. Ask questions, inspect         
                            
│   code, or use slash commands:                                                  ▅▅
                            
│                                                                                   
                            
│   • /ado: Inspect or verify Azure DevOps connection                               
                            
│   • /ado setup <org> <project> [repo]: Update Azure DevOps settings               
                            
│   • /run <ticket_id> [--dry-run]: Run pipeline on a work item                     
                            
                                                                                    
                            
┌──────────────────────────────────────────────────────────────────────────────────┐
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
│                                                                                  │
                            
└──────────────────────────────────────────────────────────────────────────────────┘
                            
                            
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
▊▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▎
    Refresh     
▊  Type a coding query or slash command (/help, /ado)...                           ▎
▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
▊▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▎
                                                                                                                         ⭘                          Azure DevOps SDLC Agent — Interactive Coding & SDLC Assistant                      14:27:46 
                               │                                                                                        
 SESSIONS                      │  │                                                                                     
                               │  │ Agent:                                                                              
 #0 running - Work Item #0     │  │                                                                                     
                               │  │   👋 Welcome to the Azure DevOps SDLC Agent!                                        
                               │  │                                                                                     
                               │  │   You are in an active interactive coding session. Ask questions, inspect           
                               │  │   code, or use slash commands:                                                  ▅▅  
                               │  │                                                                                     
                               │  │   • /ado: Inspect or verify Azure DevOps connection                                 
                               │  │   • /ado setup <org> <project> [repo]: Update Azure DevOps settings                 
                               │  │   • /run <ticket_id> [--dry-run]: Run pipeline on a work item                       
                               │                                                                                        
                               │  ┌──────────────────────────────────────────────────────────────────────────────────┐  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  │                                                                                  │  
                               │  └──────────────────────────────────────────────────────────────────────────────────┘  
                               │                                                                                        
                               │  ────────────────────────────────────────────────────────────────────────────────────  
                               │                                                                                        
 ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔              │  ▊▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▎  
     Refresh                   │  ▊  Type a coding query or slash command (/help, /ado)...                           ▎  
 ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁              │  ▊▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▎  
                               │                                                                                        
                                                                                                                        #0 running - Work Item #0   
 ^q Exit                                                                                                    ▏^p palette  ^q Exit                                                                                                    ▏^p palette  ^q Exit ▏^p palette ▊▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▎
▊  r                                                                               ▎
▊▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▎ 14:27:47 [?2004l[?7h[?1000l[?1003l[?1015l[?1006l[<u[?1049l[?25h[?1004l[?1000l[?1003l[?1015l[?1006l
```
