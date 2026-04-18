# Weather Modeling

Weather affects scoring in outdoor sports in measurable, predictable ways. For NFL and college football, wind and precipitation have well-documented effects on passing efficiency and kicking success. For MLB, temperature and wind direction affect ball carry and run scoring. For soccer, rain and heavy pitches affect pace and goal rates. Weather data is publicly available and often not fully priced into bookmaker lines, making it one of the more accessible edges for quantitative bettors.

## NFL and College Football

Weather is most impactful in football because passing is the dominant source of scoring and kicking (field goals, extra points, punts) is directly affected by wind.

### Wind Speed

Wind is the most predictive weather variable for NFL totals. Key thresholds:

| Wind speed | Effect |
|-----------|--------|
| 0–9 mph | Negligible effect on passing or kicking |
| 10–19 mph | Modest reduction in deep passing efficiency; mild kicking effect |
| 20–29 mph | Meaningful reduction in air yards, completion rate on long routes |
| 30+ mph | Severe impact; quarterbacks shorten throws; field goal accuracy drops significantly |

Studies of NFL totals markets suggest that games with sustained winds above 20 mph produce, on average, 3–5 fewer total points than similar matchups in calm conditions.

### Wind Direction

Direction matters as much as speed, particularly for kicking. Wind blowing directly into a kicker reduces effective field goal range. Wind at the kicker's back extends range. Cross-winds cause drift.

In practice, most weather-adjusted models apply a single wind speed feature rather than decomposing direction. More sophisticated models compute the headwind/tailwind component relative to the direction of each stadium's field orientation. Stadium orientation data is available for all NFL venues.

### Precipitation (Rain, Snow)

Precipitation reduces traction, affects ball handling, and impacts passing grip. It is associated with:
- Reduced completions on short-to-medium routes (ball movement in rain is less precise)
- Increased fumble rates
- Reduced scoring in high-precipitation games

Quantifying the effect is harder than wind because precipitation intensity varies and data quality is inconsistent. Light drizzle vs. heavy rain vs. snow are meaningfully different. A binary "precipitation yes/no" feature is a reasonable starting point; precipitation intensity (mm/hr) is better.

### Temperature

Cold games (below 32°F / 0°C) show a modest reduction in scoring relative to mild-weather games. The primary mechanism is reduced muscle function and grip. The effect is smaller than wind and less consistently significant across studies. Temperature below ~20°F (-7°C) shows more reliable effects.

**Key nuance**: teams acclimated to cold weather (Minnesota, Green Bay, Buffalo) are less disadvantaged than warm-weather teams playing in January. A matchup-specific temperature adjustment (weighted by each team's home climate) is more predictive than raw temperature alone.

### Indoor Stadiums

Games played in domed stadiums have no weather effects. These markets should be excluded from any weather-based feature engineering. Retractable-roof stadiums may or may not have the roof open depending on conditions.

### Weather Data Sources for NFL

- **OpenWeatherMap API**: historical and forecast weather by lat/lon with hourly resolution
- **Weather.gov**: official NWS forecasts; reliable for US locations
- **Visual Crossing**: historical weather API with stadium-level queries
- **Pro Football Reference**: historical game weather notes (less granular, but free)

Stadium coordinates for all NFL venues are publicly available. Query weather at the stadium lat/lon for the game date and time.

---

## MLB

Weather effects on baseball are more subtle but still significant, particularly for totals markets.

### Temperature and Ball Carry

Warmer air is less dense, allowing batted balls to carry farther. The rule of thumb: each 10°F increase in temperature adds approximately 1–2 feet of carry on a well-struck ball. At 90°F vs. 50°F, the difference can shift home run probability meaningfully.

Home run rates correlate with temperature across all stadiums. This effect is particularly large at Coors Field (altitude adds to it; see below).

### Wind Direction and Speed

Baseball has a clearly defined wind direction relative to each ballpark:

- **Wind blowing out to center/left/right field**: increases home run probability and run scoring
- **Wind blowing in from the outfield**: suppresses home runs, reduces scoring
- **Cross-winds**: intermediate effects

The ESPN Game Day wind tool and Baseball Savant provide pre-game wind projections for each park. For modeling, compute the dot product of wind vector and the outfield direction vector to get an effective "blowing out vs. blowing in" scalar.

### Altitude

Coors Field (Denver, ~5,280 feet elevation) has dramatically reduced air density, producing roughly 10–15% more home runs than a sea-level park under identical conditions. This is a permanent park factor, not a day-to-day weather variable, but it interacts with temperature and humidity.

### Humidity

Higher humidity (more water vapor) makes air less dense, slightly increasing carry. The effect is small — typically modeled as a minor adjustment within a full temperature-humidity composite.

### Park Factors

Weather effects interact with park dimensions. A wind-out game at Fenway (short left field) has a different impact than the same wind at Petco Park (deep dimensions). Always apply weather adjustments on top of park factor adjustments, not independently.

### Rain Delays and Game Postponements

Rain is the most operationally impactful weather variable in MLB — not because of scoring effects but because of game cancellations and delays. A rain-shortened game (called after 5 innings) produces different outcomes than a full-game result.

For modeling purposes:
- Pre-game precipitation probability is a bet-or-wait signal: in heavy rain forecasts, wait for the line to reflect the potential disruption before betting
- In-game rain delays affect pitcher usage, bullpen strategy, and player performance post-delay

---

## Soccer

Weather effects in soccer are real but smaller than in NFL or MLB. They are most impactful in top-level leagues where pitch quality is generally excellent, but more significant in lower leagues with worse playing surfaces.

### Rain and Heavy Pitches

Heavy rain leads to:
- Slower pace (ball movement affected by wet turf)
- Fewer long passing combinations (shorter, more direct play)
- Slightly reduced scoring rates in some studies (more errors, less technical play)

The effect is inconsistent across leagues and studies. It is a candidate feature to test but should not be applied without empirical validation on your specific dataset.

### Wind

Wind is far less impactful in soccer than NFL because the ball is on the ground more often. Strong winds (30+ mph) can affect long clearances and set pieces, but the effect on total goals is small.

### Temperature

Cold weather in soccer shows a very modest association with fewer goals. Not typically a significant modeling feature.

### Pitch Condition

For lower leagues and international tournaments played on non-standard surfaces (artificial turf, degraded pitches), surface type is a more important variable than atmospheric weather. Certain teams perform significantly better or worse on artificial turf.

---

## Building a Weather Feature

### Recommended Feature Set (NFL Totals)

```python
features = {
    'wind_speed_mph': float,                # sustained wind at game time
    'wind_speed_squared': float,            # captures non-linear effect at high speeds
    'precip_binary': int,                   # 1 if precipitation expected, 0 otherwise
    'precip_mm_hr': float,                  # intensity
    'temp_fahrenheit': float,
    'is_dome': int,                         # 1 for indoor stadiums (zeroes all other weather features)
    'cold_weather_home_team': float,        # interaction: home team's climate avg vs. game temp
}
```

### Validation

Weather features should be validated by:
1. Checking that each feature has a statistically significant coefficient in your model
2. Confirming the direction of the effect matches the expected sign (wind up → total down)
3. Testing out-of-sample using walk-forward validation — weather effects are consistent enough that a well-specified feature should hold up. See [`backtesting.md`](backtesting.md)

### Data Pipeline

For live deployment, pull weather forecasts for each game location 24–48 hours in advance, then update as game time approaches. Forecast accuracy for temperature and precipitation is high at 24 hours; wind forecast accuracy degrades somewhat at longer windows. Use 6-hour forecasts for final weather feature values before placing bets.
