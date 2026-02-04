# How to Update the Scatterplot Data

## 1. Locate the Data
Open `new.html` and look for the `var data = [...]` array (around line 252).

## 2. Data Structure
Each item in the list represents a bubble. Here is the template:

```javascript
{
    "id": "Name of the Technology",  // The text label
    "x": 31.32,                      // Horizontal position (Relatedness Density)
    "y": 61,                         // Vertical position (Complexity)
    "rca": 1.83,                     // Value determining color definition (Optional if you just use 'color')
    "color": "#679A67",              // Bubble color (Hex code or name)
    "value": 0.5,                    // Size of the bubble (keep 0.5 for uniform size)
    
    // Optional Manual Overrides:
    "labelDirection": "top-right",   // Force label position: 'right', 'left', 'above', 'below', 
                                     // 'top-right', 'bottom-right', 'bottom-left', 'top-left'
    "labelColor": "gray"             // Force text color (e.g., 'gray', 'black', or hex)
}
```

## 3. Changing Axis Limits (Optional)
If your new data falls outside the current view (0-100 on X-axis), you might need to adjust the domain range around **line 595**:

```javascript
const xDomain = [-5, 105]; // Adjust these numbers if dots get cut off horizontally
```
*The Y-axis adjusts automatically based on your data.*

## 4. Tips
*   **Text Collisions**: The chart tries to place labels automatically. If a label is overlapping or greyed out, use `"labelDirection"` to force it into a free space.
*   **Greyed Labels**: Labels turn grey/transparent if the system detects a collision. Providing a manual direction overrides the grey-out behavior (unless it's truly unreadable).
