import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV
df = pd.read_csv('ipl_2025_final.csv')

# Standardize column names
df.columns = df.columns.str.strip()

# --- Chart 1: Proportion of Fours vs Sixes ---

# Calculate total boundaries
df['Team 1 Total Boundaries'] = df['Team 1 Fours'] + df['Team 1 Sixes']
df['Team 2 Total Boundaries'] = df['Team 2 Fours'] + df['Team 2 Sixes']

# Create team-specific records
team1_boundaries = df[['Match', 'Team 1 Fours', 'Team 1 Sixes', 'Team 1 Total Boundaries']].copy()
team2_boundaries = df[['Match', 'Team 2 Fours', 'Team 2 Sixes', 'Team 2 Total Boundaries']].copy()

# Extract team names (already abbreviated in 'Match')
team1_boundaries['Team'] = team1_boundaries['Match'].apply(lambda x: x.split('vs')[0].strip())
team2_boundaries['Team'] = team2_boundaries['Match'].apply(lambda x: x.split('vs')[1].strip())

# Combine both innings
boundaries = pd.concat([
    team1_boundaries.rename(columns={'Team 1 Fours': 'Fours', 'Team 1 Sixes': 'Sixes'}),
    team2_boundaries.rename(columns={'Team 2 Fours': 'Fours', 'Team 2 Sixes': 'Sixes'})
])

# Group and calculate percentages
grouped = boundaries.groupby('Team').sum()
grouped['Total Boundaries'] = grouped['Fours'] + grouped['Sixes']
grouped['Fours %'] = (grouped['Fours'] / grouped['Total Boundaries']) * 100
grouped['Sixes %'] = (grouped['Sixes'] / grouped['Total Boundaries']) * 100

# Plot 1: Proportion of boundary types
grouped[['Fours %', 'Sixes %']].sort_values('Sixes %').plot(kind='barh', stacked=True, figsize=(12,8))
plt.title('Proportion of Fours vs Sixes by Team (All Matches)')
plt.xlabel('Percentage of Total Boundaries')
plt.legend(loc='lower right')
plt.tight_layout()
plt.show()
plt.close()

# --- Chart 2: Winning Factors - Average Powerplay, Fours, and Sixes ---

# Extract winning team name (already abbreviated)
df['Winning Team'] = df['Winner'].apply(lambda x: x.split('Won')[0].strip())

winning_stats = []

for idx, row in df.iterrows():
    try:
        team1 = row['Match'].split('vs')[0].strip()
        team2 = row['Match'].split('vs')[1].strip()
        winner = row['Winning Team']

        if winner == team1:
            winning_stats.append({
                'Team': team1,
                'Powerplay Runs': row['Team 1 Powerplay Runs'],
                'Fours': row['Team 1 Fours'],
                'Sixes': row['Team 1 Sixes']
            })
        elif winner == team2:
            winning_stats.append({
                'Team': team2,
                'Powerplay Runs': row['Team 2 Powerplay Runs'],
                'Fours': row['Team 2 Fours'],
                'Sixes': row['Team 2 Sixes']
            })
        else:
            print(f"Warning: Could not match winner {winner} for {row['Match']}")
    except Exception as e:
        print(f"Error processing row {idx}: {e}")

winning_df = pd.DataFrame(winning_stats)

if winning_df.empty:
    print("\n⚠️ No winning data available to plot. Please check data matching!")
else:
    agg_winning = winning_df.groupby('Team').mean()
    agg_winning[['Powerplay Runs', 'Fours', 'Sixes']].plot(kind='bar', figsize=(14,7))
    plt.title('Winning Teams - Average Powerplay, Fours, and Sixes')
    plt.ylabel('Average per Match')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    plt.close()

# --- Chart 3: Teams hitting most sixes in losses ---

losing_stats = []

for idx, row in df.iterrows():
    try:
        team1 = row['Match'].split('vs')[0].strip()
        team2 = row['Match'].split('vs')[1].strip()
        winner = row['Winning Team']

        if winner == team1:
            losing_stats.append({'Team': team2, 'Sixes in Loss': row['Team 2 Sixes']})
        elif winner == team2:
            losing_stats.append({'Team': team1, 'Sixes in Loss': row['Team 1 Sixes']})
    except Exception as e:
        print(f"Error processing row {idx} for losses: {e}")

losing_df = pd.DataFrame(losing_stats)

if losing_df.empty:
    print("\n No losing data available to plot.")
else:
    agg_losing = losing_df.groupby('Team').mean()
    agg_losing['Sixes in Loss'].sort_values(ascending=False).plot(kind='bar', figsize=(14,7))
    plt.title('Average Sixes by Teams When They Lose')
    plt.ylabel('Average Sixes in Defeat')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    plt.close()

# --- Chart 4: Boundary % Difference Between Winner and Loser ---

boundary_diff = []

for idx, row in df.iterrows():
    try:
        team1 = row['Match'].split('vs')[0].strip()
        team2 = row['Match'].split('vs')[1].strip()
        winner = row['Winning Team']

        team1_boundaries = row['Team 1 Fours'] + row['Team 1 Sixes']
        team2_boundaries = row['Team 2 Fours'] + row['Team 2 Sixes']

        if winner == team1:
            boundary_diff.append(team1_boundaries - team2_boundaries)
        elif winner == team2:
            boundary_diff.append(team2_boundaries - team1_boundaries)
    except Exception as e:
        print(f"Error processing row {idx} for boundary diff: {e}")

if not boundary_diff:
    print("\n No boundary difference data to plot.")
else:
    plt.figure(figsize=(10,6))
    plt.hist(boundary_diff, bins=10, edgecolor='black')
    plt.title('Boundary Count Difference (Winner - Loser)')
    plt.xlabel('Boundary Difference')
    plt.ylabel('Number of Matches')
    plt.axvline(x=sum(boundary_diff)/len(boundary_diff), color='red', linestyle='dashed', linewidth=2, label='Mean Difference')
    plt.legend()
    plt.tight_layout()
    plt.show()
