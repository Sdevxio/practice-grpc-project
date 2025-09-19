class AppleScripts:
    """
    A class to handle AppleScript commands.
    """
    APPLESCRIPT_LOG_OUT_USER = '''
    tell application "System Events"
        tell process "Finder"
            -- Click the Apple menu
            click menu bar item 1 of menu bar 1
            delay 1

            -- Look for "Log Out" menu item (accounting for username variations)
            set appleMenu to menu 1 of menu bar item 1 of menu bar 1
            set menuItems to menu items of appleMenu

            repeat with menuItem in menuItems
                set itemName to name of menuItem
                if itemName contains "Log Out" then
                    -- Click the Log Out menu item
                    click menuItem
                    delay 1

                    -- Handle confirmation dialog using multiple methods
                    tell application "System Events"
                        -- Try different approaches to confirm logout
                        repeat 3 times
                            delay 0.5
                            try
                                -- Method 1: Direct button click by name
                                click button "Log Out" of front window
                                return "Log Out confirmed with button click"
                            end try
                            try
                                -- Method 2: Try clicking default button
                                click button 1 of front window
                                return "Log Out confirmed with default button"
                            end try
                            try
                                -- Method 3: Try keyboard shortcut
                                keystroke return
                                return "Log Out confirmed with Return key"
                            end try
                        end repeat
                    end tell
                    return "Logout sequence initiated"
                end if
            end repeat

            -- If we get here, Log Out wasn't found
            key code 53 -- Press Escape to close menu
            return "Log Out menu item not found"
        end tell
    end tell
    '''