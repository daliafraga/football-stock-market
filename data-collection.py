import pandas as pd
from datetime import datetime, timedelta
import random
import matplotlib.pyplot as plt


# need to preprocess this file to contain only necessary data
filename = "2023_2024 data.csv"

# a function to return if a team has won, drawn or lost based on goals scored
def match_result(hg, ag):
    if hg > ag:
        return("W")
    elif hg < ag:
        return("L")
    else:
        return("D")

def preprocess(filename=filename):
    # read the data in
    df = pd.read_csv(filename)

    # remove any unnecessary columns
    desired_columns = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"]
    unwanted_columns = []

    for column in df.columns:
        if column not in desired_columns:
            unwanted_columns.append(column)

    df = df.drop(unwanted_columns, axis=1)
    
    # rename the column names
    column_names = ["Date", "Home Team", "Away Team", "Home Goals", "Away Goals"]
    df.columns = column_names

    # add the results for both teams
    df["Home Result"] = df.apply(lambda r: match_result(r["Home Goals"], r["Away Goals"]),axis=1)
    df["Away Result"] = df.apply(lambda r: match_result(r["Away Goals"], r["Home Goals"]), axis=1)

    # let's change the dtypes of home result & away result (saves memory)
    df["Home Result"] = df["Home Result"].astype("category")
    df["Away Result"] = df["Away Result"].astype("category")

    # seperate the two teams (home & away) from each row and assign each an individual row
    home_teams = df[["Date", "Home Team", "Home Goals", "Away Goals", "Home Result"]]
    away_teams = df[["Date", "Away Team", "Away Goals", "Home Goals", "Away Result"]]

    home_teams.columns = ["Date", "Team", "Goals Scored", "Goals Conceded", "Result"]
    away_teams.columns = ["Date", "Team", "Goals Scored", "Goals Conceded", "Result"]

    df = pd.concat([home_teams, away_teams])

    # date formatting & sorting
    df.Date = pd.to_datetime(df.Date, format="%d/%m/%Y")
    df = df.sort_values(["Date", "Team"])

    # assign weeks by the difference in days between actual & first game
    first_game = df.Date.min()
    df["Week"] = ((df["Date"] - first_game).dt.days // 7) + 1
    
    # re-organising the columns and sorting by week & team
    df = df.drop("Date", axis=1)
    ordered_columns = ["Week", "Team", "Result", "Goals Scored", "Goals Conceded"]
    df = df[ordered_columns]
    df.sort_values(["Week", "Team"])

    df = df.groupby(["Week", "Team"]).agg(
        Win=("Result", lambda x: (x=="W").sum()), # returns a true/false so can sum to get number of W/D/L
        Draw = ("Result", lambda x: (x=="D").sum()),
        Loss = ("Result", lambda x: (x=="L").sum()),
        Scored = ("Goals Scored", "sum"),
        Conceded = ("Goals Conceded", "sum")
    ).reset_index()

    # calculate weekly percentage changes for each team per game
    df["% Change"] = (df.Win * 0.05
                               + df.Draw * 0
                               - df.Loss * 0.05
                               + df.Scored * 0.005
                               - df.Conceded * 0.005)
    
    df["% Multiplier"] = df["% Change"] + 1

    # calculate the cumulative multiplier from week 1
    df["Cumulative Multiplier"] = df.groupby("Team")["% Multiplier"].cumprod()

    return(df)


# finished preprocessing data, what to do next:
# ... calculate percentage change in stocks depending on results, goals scored & goals conceded
# ... group each team so can calculate value for different weeks given an initial investment
# ... create investment strategies using different teams
# ... plot results


def stock_information(df): 

    # set an IPO for each club (based on my opinions here!)
    start_prices = {
        "Arsenal" : 150,
        "Aston Villa" : 100,
        "Bournemouth" : 100,
        "Brentford" : 100,
        "Brighton" : 100,
        "Burnley" : 70,
        "Chelsea" : 120,
        "Crystal Palace" : 100,
        "Everton" : 100,
        "Fulham" : 90,
        "Liverpool" : 140,
        "Luton" : 60,
        "Man City" : 150,
        "Man United" : 100,
        "Newcastle" : 120,
        "Nott'm Forest" : 100,
        "Sheffield United" : 50,
        "Tottenham" : 100,
        "West Ham" : 90,
        "Wolves" : 90
        }

    # fill in missing weeks
    weeks = range(1, df["Week"].max()+1)
    teams = df["Team"].unique()

    # add a week 0 so you can invest before the season starts
    weeks = [0] + list(weeks)

    # use a multi_index to give each team every week. leads to some weeks having Nan values, which we can fill later!
    multi_index = pd.MultiIndex.from_product([weeks, teams], names=["Week", "Team"])
    df = df.set_index(["Week", "Team"]).reindex(multi_index).reset_index()

    # build a stock price column...
    # ... and normalise so that each stock has a stock price of £100 in week 1
    df["Stock Price"] = df.apply(lambda row: start_prices[row["Team"]] * (row["Cumulative Multiplier"]) if row["Week"] > 0 else start_prices[row["Team"]], axis=1)

    # for the weeks where a team doesn't play stock price (currently NaN) will just be previous week's stock price
    df["Stock Price"] = (df.groupby("Team")["Stock Price"]
                         .transform(lambda s: s.ffill().bfill())) # forward fill and back fill if a team missed a game in the first few weeks

    # compress multiple matches into one weekly value
    df = (df.groupby(["Week", "Team"], as_index=False)
          .agg({"Stock Price" : "last"})) # taking the last value (could do mean if i wanted to!)
    
    # add a week zero so you can invest in a team before the first games
    

    return(df)

ii = stock_information(preprocess())

# let's create a Portfolio object where we can define a ton of investment related actions, like buy, sell, etc

class Portfolio:
    # create some functions to display cash, holdings & history
    def __init__(self, cash=1000):
        self.cash = cash # cash available in portfolio
        self.holdings = {} # this dictionary will have team : number of shares
        self.history = []

    # access how much cash is available in the portfolio
    def cash(self):
        return("You currently have £" + str(self.cash) + " available.")

    # define the buy action
    def buy(self, team, week, amount, df):
        # need to make sure you can buy more than the cash availalble
        if amount > self.cash:
            print("Not enough cash available to buy this stock!")
            return
        
        # locate the stock price of the desired team
        stock_price = df[(df.Team == team) & (df.Week == week)]["Stock Price"].values[0]
        
        # calculate the number of shares that will be bought
        num_of_shares = amount / stock_price
        #print("Buy " + str(round(num_of_shares,2)) + " shares at £" + str(round(stock_price,2)))

        # add this information to holdings
        self.holdings[team] = self.holdings.get(team, 0) + round(float(num_of_shares), 2)
        #print("Holdings: " + str(self.holdings))

        # take away the used cash from the available in the portfolio
        self.cash -= amount
        #print("Cash Remaining: " + str(self.cash))

        # record this transaction in the history log
        self.history.append(("BUY", team, week, amount, round(float(stock_price),2)))
        #print("Recent History: " + str(self.history))

    # define the sell action
    def sell(self, team, week, amount, df):
        # make sure you can't sell a stock you don't own (also need to check that you can't sell more than you own)
        if team not in self.holdings:
            print("You don't own any of this stock to sell!")
            return 
        
        # locate the stock price
        stock_price = df[(df.Team == team) & (df.Week == week)]["Stock Price"].values[0]

        # calculate the number of shares
        num_of_shares = amount / stock_price

        # subtract this information from the holdings
        self.holdings[team] = self.holdings.get(team, 0) - round(float(num_of_shares), 2)
        #print("Holdings: " + str(self.holdings))
    
        # add this cash to the availalbe cash in the portfolio
        self.cash += amount
        #print("Cash Remaining: " + str(self.cash))

        # record this transaction in the history log
        self.history.append(("SELL", team, week, amount, round(float(stock_price), 2)))
        #print("Recent History: " + str(self.history))

    # return the value of the total portfolio for any given week
    def value(self, week, df):

        # calculate the value of all current holdings at that given week
        stock_total_value = 0
        for team in self.holdings:
            stock_total_value += (self.holdings[team] * df[(df.Team == team) & (df.Week == week)]["Stock Price"].values[0])

        total_value = self.cash + stock_total_value
        return(round(float(total_value),2))



# stimulate different investing strategies

# the big 6 (arsenal, chelsea, liverpool, man city, man u, tottenham)

def big6(cash_to_invest, df):
    """Input the stock prices dataframe and implement a Big 6 investment strategy,
    i.e. investing a desired amount equally into each of the Big 6 and it's weekly value."""
    
    ptf = Portfolio(cash_to_invest)

    big6_teams = ["Arsenal", "Chelsea", "Liverpool", "Man City", "Man United", "Tottenham"]
    
    split_cash = cash_to_invest / len(big6_teams)

    for team in big6_teams:
        ptf.buy(team, 0, split_cash, df)

    weeks = list(range(0,42))

    weekly_values = []
    for week in weeks:
        weekly_values.append(ptf.value(week, df))

    return(pd.DataFrame({"Week" : weeks,
                        "Big 6 Portfolio Value" : weekly_values}))



# the underdogs (sheffield united, burnley, luton & fulham)
def underdogs(cash_to_invest, df):
    ptf = Portfolio(cash_to_invest)

    underdogs = ["Sheffield United", "Burnley", "Luton", "Fulham"]

    split_cash = cash_to_invest / len(underdogs)

    for team in underdogs:
        ptf.buy(team, 0, split_cash, df)

    weeks = list(range(0,42))

    weekly_values = []
    for week in weeks:
        weekly_values.append(ptf.value(week, df))

    return(pd.DataFrame({"Week" : weeks,
                        "Underdogs Portfolio Value" : weekly_values}))


# a mixed portfolio (choose 5 teams at random)
def mixed(cash_to_invest, df):

    ptf = Portfolio(cash_to_invest)
    # select 5 teams randomly
    teams = df.Team.unique()
    selected_teams = random.choices(teams,k=5)

    split_cash = cash_to_invest / len(selected_teams)

    for team in selected_teams:
        ptf.buy(team, 0, split_cash, df)

    weeks = list(range(0,42))

    weekly_values = []
    for week in weeks:
        weekly_values.append(ptf.value(week, df))

    return(pd.DataFrame({"Week" : weeks,
                        "Mixed Portfolio Value" : weekly_values}))


# a benchmark portfolio (invest equally into all teams)
def benchmark(cash_to_invest, df):
    ptf = Portfolio(cash_to_invest)

    teams = df.Team.unique()
    
    split_cash = cash_to_invest / len(teams)

    for team in teams:
        ptf.buy(team, 0, split_cash, df)

    weeks = list(range(0,42))

    weekly_values = []
    for week in weeks:
        weekly_values.append(ptf.value(week, df))

    return(pd.DataFrame({"Week" : weeks,
                        "Benchmark Portfolio Value" : weekly_values}))


# visualisations

# line chart to show portfolio value over time

def line_analysis():
# just changing all the indexes so it will be easier to combine dataframes
    dfs = [big6(1000,ii).set_index("Week"),
        underdogs(1000,ii).set_index("Week"),
        mixed(1000, ii).set_index("Week"),
        benchmark(1000,ii).set_index("Week")]

    all_strategies = pd.concat(dfs, axis=1)

    #plt.legend(loc="upper left", bbox_to_anchor=(1,1))
    ax = all_strategies.plot(figsize=(10,3), color = ["red", "blue", "green", "orange"],
                    title="Portfolio Value over Time",
                    ).legend(loc="upper left", bbox_to_anchor=(1,1))

    # plot a baseline at 1000 for reference
    plt.axhline(y=1000, color="gray", linestyle="--", linewidth=1)
    plt.xticks(range(0,len(all_strategies), 5))

    plt.show()


# bar charts to show average weekly returns for each of the strategies


def bar_analysis():

    # calculate the average weekly returns in each dataframe
    big6_returns = big6(1000, ii).set_index("Week").pct_change()
    avg_big6_returns = big6_returns.mean()

    underdogs_returns = underdogs(1000, ii).set_index("Week").pct_change()
    avg_underdogs_returns = underdogs_returns.mean()

    mixed_returns = mixed(1000, ii).set_index("Week").pct_change()
    avg_mixed_returns = mixed_returns.mean()

    benchmark_returns = benchmark(1000, ii).set_index("Week").pct_change()
    avg_benchmark_returns = benchmark_returns.mean()

    # combine into a new dataframe
    all = pd.concat([avg_benchmark_returns,avg_big6_returns, avg_mixed_returns, avg_underdogs_returns], axis=0)
    all = (all * 100).sort_values()
    
    # manipulate the presentation of the bar chart
    colours = ["blue", "green", "orange", "red"]
    fig, ax = plt.subplots(figsize=(8,4))
    bars = ax.bar(all.index, all.values, color=colours)

    plt.xticks(rotation=0)
    ax.bar_label(bars, labels=[f"{v:.2f}%" for v in all.values])

    ax.set_title("Average Weekly Percentage Returns")
    ax.set_ylabel("Average Weekly Return (%)")
    ax.set_xticklabels(["Underdogs", "Benchmark", "Mixed", "Big 6"])
    plt.show()


#line_analysis()
#bar_analysis()


# quick performance metrics

# final percentage return


big6_percentage_return = (((big6(1000,ii)["Big 6 Portfolio Value"].values[-1])-(big6(1000,ii)["Big 6 Portfolio Value"].values[0])) / (big6(1000,ii)["Big 6 Portfolio Value"].values[0])) * 100
#print(big6_percentage_return)

underdogs_percentage_return = (((underdogs(1000,ii)["Underdogs Portfolio Value"].values[-1])-(underdogs(1000,ii)["Underdogs Portfolio Value"].values[0])) / (underdogs(1000,ii)["Underdogs Portfolio Value"].values[0])) * 100
#print(underdogs_percentage_return)

mixed_percentage_return = (((mixed(1000,ii)["Mixed Portfolio Value"].values[-1])-(mixed(1000,ii)["Mixed Portfolio Value"].values[0])) / (mixed(1000,ii)["Mixed Portfolio Value"].values[0])) * 100
#print(mixed_percentage_return)

benchmark_percentage_return = (((benchmark(1000,ii)["Benchmark Portfolio Value"].values[-1])-(benchmark(1000,ii)["Benchmark Portfolio Value"].values[0])) / (benchmark(1000,ii)["Benchmark Portfolio Value"].values[0])) * 100
#print(benchmark_percentage_return)

print(ii[ii["Week"] == 41])