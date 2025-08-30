What if football teams were stocks?

Recently, I've been working on a project where I re-imagined Premier League teams as if they had stock prices. 
- Every team's "share price" moves with their weekly performance, depending on W/D/L and goals scored/conceded.
- I built different investment strategies: Big 6, Underdogs, Mixed (Random), and a benchmark strategy.
- I tracked how £1,000 invested before the season would have grown over the season.

I preprocessed a 2023/2024 season dataset, calculating a variety of percentage changes and then assigned share prices based on performance. After creating different strategies, I could simulate how they would perform, calculate simple return percentages and plotted a couple of graphs to demonstrate how the market moved. Here are the key takeaways: 

- The Big 6 outperformed massively.

- The Underdogs struggled on average (risk ≠ always reward!).

- Diversification proves valuable compared to concentrated bets.



What next? 

- The stock market model I created is very linear and doesn't accurately represent the volatility we see in real life. Some adaptations that I need to make include refining for home vs away games, for typically stronger teams against weaker teams, and even for heavily injured teams.
- More data analysis, including deeper risk metrics such as volatility and Sharpe ratios.
- Improving the visualisations. Currently the performance of the Big 6 silences the movements in the other strategies. I could even look to use the Seaborn module to create more aesthetic and clearer visuals.

This has been a cool way to combine data science, finance and football analysis!



