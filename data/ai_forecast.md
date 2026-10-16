# The AI forecast run

This file records the AI run used for requirement 7. The prompt, the reply and the
run details are reproduced without any change.

## Run details

| Item | Value |
|---|---|
| Date of run | 16 October 2026 |
| Model | Claude Sonnet 5, model id `claude-sonnet-5` |
| Effort setting | Low |
| Tools available to the model | None. The model was told not to use tools and used none. |
| Information given | The ten annual import values and the unit, and nothing else. |
| Information withheld | The change point analysis, the refinery closures, the research notes, the export side, the target path and both of my forecast methods. |

The model saw no part of this project. It received ten numbers. This keeps the
comparison honest, because any agreement or disagreement comes from the data alone.

## The prompt, word for word

```
Australian imports of SITC subcategory 33, Petroleum, petroleum products and related
materials. Annual values in millions of Australian dollars.

2016 23315
2017 29365
2018 39947
2019 38357
2020 22720
2021 34044
2022 65082
2023 60057
2024 56183
2025 52742

Do two things. Keep the whole answer under 200 words. Answer directly from the numbers
given. Do not use any tools.

1. Describe the trend between 2016 and 2025.
2. Forecast the value for each year from 2026 to 2030. Give one number per year in
millions of Australian dollars.
```

## The reply, word for word

```
1. Imports rose overall from 2016 to 2025. Values climbed from 23315 in 2016 to a peak
of 65082 in 2022, with a dip in 2020 to 22720, likely due to reduced demand that year.
After 2022, values fell each year to 52742 in 2025, though 2025 is still more than
double the 2016 level.

2. Forecast for 2026 to 2030, based on the recent downward trend from 2022 to 2025 (an
average fall of about 4113 per year):

2026: 48600
2027: 44500
2028: 40400
2029: 36300
2030: 32200
```

## What the AI got right

1. It read the shape of the decade correctly. It found the 2022 peak, the 2020 dip and
   the three year decline after 2022.
2. It noticed that 2025 is still more than double the 2016 level.
3. It stated its method. The forecast extrapolates the 2022 to 2025 fall of about 4,113
   million each year. A reader can check that claim.

## Where the AI and this analysis disagree

The AI fits only the last four years. This analysis fits all ten. The two choices point
in opposite directions.

| Year | AI forecast | My linear trend | My CAGR method | Gap, AI less linear |
|---|---|---|---|---|
| 2026 | 48,600 | 63,668 | 57,749 | -15,068 |
| 2027 | 44,500 | 67,575 | 63,232 | -23,075 |
| 2028 | 40,400 | 71,482 | 69,236 | -31,082 |
| 2029 | 36,300 | 75,389 | 75,809 | -39,089 |
| 2030 | 32,200 | 79,296 | 83,007 | -47,096 |

By 2030 the two answers differ by 47,096 million dollars, which is more than the whole
2016 import value. The AI forecasts a fall of 39% from 2025. My linear trend forecasts a
rise of 50%.

## What the AI could not know

1. The 2020 dip and the 2022 peak are price events, not demand events. The import and
   the export side of subcategory 33 move together at a correlation of 0.91, which only
   the two way data shows. The AI received the import side alone.
2. Australian refinery closures in 2020 and 2021 cut domestic refining capacity. That
   raises the refined product share of imports and puts a floor under the volume. The AI
   had no access to this.
3. The linear fit over ten years has an R squared of only 0.589. The series is too noisy
   for any confident five year forecast. The AI gave five exact numbers and no error
   range, which reads as more certain than the data allows.

## The honest conclusion

Neither forecast deserves confidence. The AI anchored on four years and produced a
steady fall. My linear trend anchored on ten years and produced a steady rise. The real
finding is that a ten point annual series driven by a world price cannot support a five
year point forecast. The target path matters more than the forecast, because the target
is a decision and the forecast is a guess.
