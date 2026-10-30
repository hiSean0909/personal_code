# Toolbox Specification

## Goal and Scope

Create an Android app named Magic Box that provides a home screen, Display and Ruler tools, and three small games: 2048, Minesweeper, and Flappy Bird. All features run locally without a network connection or account.

## Functional Requirements

### Home Screen and Search

- Show bottom navigation tabs for Tools, Search, and Games, and open Search by default at launch
- Show a search field at the top of Tools and list Display and Ruler below it; filter the list by name
- Show a search field in the center of Search and search all tools and games by name
- Show a search field at the top of Games and list 2048, Minesweeper, and Flappy Bird below it; filter the game list by name
- Match names without regard to English letter case and allow the user to open a tool from search results
- Allow the user to return to the home screen from each tool or game

### Display

- Allow the user to enter text and configure its size, color, italic style, and background color
- Show the configured text on a full-screen display, scrolling horizontally in a continuous loop so longer text can be read
- Allow the user to return from the display to edit the settings

### Ruler

- Show metric markings in centimeters and millimeters along the left edge and imperial markings in inches and subdivisions along the right edge, starting from the same zero point
- Initially scale the markings using the device-reported screen dimensions
- Allow the user to calibrate the scale against a physical ruler and save the calibration for later use

### 2048

- Use a 4 by 4 board and swipe to move and merge matching numbered tiles
- Display the cumulative score and add the resulting tile value for each merge, such as 4 points for merging two 2 tiles
- Allow the user to start a new game
- Notify the user when a 2048 tile is reached or no moves remain

### Minesweeper

- Use a 9 by 9 board with 10 mines
- Tap to reveal a cell and long-press to mark a suspected mine with a small red flag
- Display the win or loss result and allow the user to start a new game

### Flappy Bird

- Tap to make the bird rise and navigate around obstacles
- Display the score and elapsed running time, end the game on collision, and allow the user to start a new game
- Increase obstacle speed and difficulty progressively as running time grows
- Stop the timer while paused and reset it when starting a new game

## Compatibility and Delivery

- Support Android 10 (API 29) and later by default
- Use English for interface text and Magic Box as the Android app name
- Provide an APK for the user to test on the vivo X300
- Verify the phone's Android version during development and record device test feedback

## Acceptance Criteria

- The app installs and opens on a supported Android device without requiring a network connection or account
- The app opens on Search, and all three bottom navigation tabs show their specified search fields and content
- Name searches are case-insensitive, filter the appropriate tools, and allow matching tools to be opened
- Tools and Search can open Display and Ruler, and the user can return to the home screen from each tool or game
- Display applies the configured text, size, colors, and italic style on a full-screen, horizontally scrolling display and allows the user to return to editing
- Ruler shows both measurement systems with a shared zero, and its saved calibration can be checked against a physical ruler on the vivo X300
- Each game supports the controls, scoring or result indication, and restart behavior described above
- 2048 adds the resulting tile value to the score for each merge, and Minesweeper displays a red flag for marked cells
- Flappy Bird displays elapsed running time, pauses and resets the timer as specified, and becomes progressively harder over time
- The user can test all three games on the vivo X300, and feedback is recorded

## Open Questions

- The user installed and tried the first version and requested the changes specified above
- The vivo X300 Android version and test results for the current iteration must be confirmed during development and delivery
