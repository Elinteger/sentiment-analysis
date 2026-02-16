import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

def prep_data(data):
    # vis 1
    sentiment_brand_dict = {}

    for _, row in data.iterrows():
        brand = row["keyword"]
        sentiment = row["sentiment"]

        if brand not in sentiment_brand_dict:
            sentiment_brand_dict[brand] = {"pos": 0, "neg": 0, "total": 0}

        if sentiment == "positive":
            sentiment_brand_dict[brand]["pos"] += 1
        else:
            sentiment_brand_dict[brand]["neg"] += 1

        sentiment_brand_dict[brand]["total"] += 1

    brand_df = pd.DataFrame([(brand, counts["pos"], counts["neg"], counts["total"]) for brand, counts in sentiment_brand_dict.items()], columns=["brand", "positive", "negative", "total"])
    brand_df["positive_ratio"] = (brand_df["positive"]/brand_df["total"]).round(4)
    brand_df["negative_ratio"] = 1 - brand_df["positive_ratio"]


    # vis 2
    grouped_df = data.groupby(["subreddit", "keyword", "sentiment"]).size().reset_index(name="count")
    sub_df = grouped_df.pivot_table(index=['subreddit', 'keyword'], columns='sentiment', values='count', fill_value=0).reset_index()
    sub_df = sub_df.astype({'positive': 'int', 'negative': 'int'})

    sub_df.columns.name = None
    sub_df["total"] = sub_df["positive"] + sub_df["negative"]
    sub_df["positive_ratio"] = (sub_df["positive"]/sub_df["total"]).round(4)
    sub_df["negative_ratio"] = 1 - sub_df["positive_ratio"]
    # swaparoo
    sub_df["positive"], sub_df["negative"] = sub_df["negative"], sub_df["positive"]
    sub_df = sub_df.rename(columns={"positive": "temp_column", "negative": "positive"})
    sub_df = sub_df.rename(columns={"temp_column": "negative"})

    # vis 3
    comment_count = len(data)

    print(f"Dataframe Brand - Vis 1:\n{brand_df}")
    print("--------------------------------------------------------------------------------------------------")
    print(f"Dataframe Sub - Vis 2:\n{sub_df}")
    print("--------------------------------------------------------------------------------------------------")
    print(f"Total amount of comments: {comment_count}")

    return brand_df, sub_df, comment_count
    

def vis_one(data, total):
    df = data.sort_values(by="positive_ratio", ascending=True)
    print(df)
    brands = [ 'Bianchi', 'BMC',
                'Cannondale', 'Canyon', 'Cervelo', 'Cinelli', 'Colnago', 'Cube',
                 'Giant', 
                  'Merida', 
                   'Orbea', 
                    'Pinarello', 
                     'Ridley', 'Rose', 
                      'Scott', 'Specialized', 
                       'Trek', 
                        'Wilier']
    # plot
    fig, ax = plt.subplots(figsize=(12,10))

    bar_width = 0.9
    brands = df["brand"]
    positive_ratios = df["positive_ratio"]
    negative_ratios = df["negative_ratio"]

    bars_positive = ax.barh(brands, positive_ratios, color="mediumseagreen", edgecolor='white', height=bar_width)
    bars_negative = ax.barh(brands, negative_ratios, left=positive_ratios, color='tomato', edgecolor='white', height=bar_width) 

    for bar, brand in zip(bars_positive, brands):
        width = bar.get_width()
        ax.text(width - 0.01, bar.get_y() + bar.get_height()/2 - 0.05, f'{width:.1%}', 
            ha='right', va='center', color='white', weight='bold')
        # ax.text(0.02, bar.get_y() + bar.get_height()/2, brand, 
        #     ha='left', va='center', color='black', weight='bold')
        
    for bar in bars_negative:
        width = bar.get_width()
        ax.text(bar.get_x() + width + 0.05, bar.get_y() + bar.get_height()/2, f'{width:.1%}', 
            ha='left', va='center', color='white', weight='bold')
        
    # for final render
    ax.scatter([], [], color='mediumseagreen', label='positive', marker='o', edgecolor='white', s=100)
    ax.scatter([], [], color='tomato', label='negative', marker='o', edgecolor='white', s=100)
    legend = ax.legend(loc='upper right', fontsize=12, bbox_to_anchor=(0.96, 1.05))
    for text in legend.get_texts():
        text.set_position((text.get_position()[0] - 10, text.get_position()[1] - 2))  # Adjust y-position
        


    plt.title("Cycling Brand Sentiment", loc='left', fontsize= 20, weight='bold')
    plt.text(0.165, 0.97, 'r/cycling, r/bicycling, r/RoadBikes', transform=ax.transAxes, ha='center', fontsize=13, style='italic')
    ax.axis('off')

    plt.show()


def vis_two(data, total):
    data = data[data['total'] >= 100]
    subreddits = data['subreddit'].unique()

    fig, axes = plt.subplots(len(subreddits), 2, figsize=(14, 6 * len(subreddits)), gridspec_kw={'hspace': 0.4})
    if len(subreddits) == 1:
        axes = [axes]

    for idx, subreddit in enumerate(subreddits):
        sub_df = data[data['subreddit'] == subreddit]

        top_3_liked = sub_df.nlargest(3, 'positive_ratio')
        
        top_3_hated = sub_df.nlargest(3, 'negative_ratio')
        
        sns.barplot(x='positive_ratio', y='keyword', data=top_3_liked, ax=axes[idx][0], palette='viridis')
        sns.barplot(x='negative_ratio', y='keyword', data=top_3_hated, ax=axes[idx][1], palette='magma')
        
        axes[idx][0].set_title(f'Top 3 Most Liked Bike Brands in r/{subreddit}', fontweight='bold')
        axes[idx][0].set_xlim(0, 1)
        axes[idx][0].set_xlabel('Positive Ratio')
        axes[idx][0].set_ylabel('Bike Brand')
        
        axes[idx][1].set_title(f'Top 3 Most Disliked Bike Brands in r/{subreddit}', fontweight='bold')
        axes[idx][1].set_xlim(0, 1)
        axes[idx][1].set_xlabel('Negative Ratio')
        axes[idx][1].set_ylabel('Bike Brand')
        
        for i in axes[idx][0].patches:
            axes[idx][0].annotate(f'{i.get_width() * 100:.2f}%', 
                                (i.get_width() - 0.005, i.get_y() + i.get_height() / 2), 
                                va='center', ha='right', fontsize=10, fontweight='bold', color='white')

        for i in axes[idx][1].patches:
            axes[idx][1].annotate(f'{i.get_width() * 100:.2f}%', 
                                (i.get_width() - 0.005, i.get_y() + i.get_height() / 2), 
                                va='center', ha='right', fontsize=10, fontweight='bold', color='white')

    plt.figtext(0.5, 0.01, "Note: Brands with fewer than 100 comments are filtered out.", ha='center', fontsize=12, fontstyle='italic')

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.show()




def vis_three(data, total):
   # calculate maximum comments
    max_comments = max(data['total']) * 1.1

    # calculate controversy score
    data['controversy_score'] = (data['negative'] / data['total']) * (1 - (data['total'] / max_comments))

    # sort data by controversy score
    df_sorted = data.sort_values(by='controversy_score', ascending=False)

    # number of variables (brands) and angles for the radar chart
    brands = df_sorted['brand']
    values = df_sorted['controversy_score']
    num_vars = len(brands)

    # compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # repeat the first value to close the circle
    values = np.concatenate((values, [values[0]]))
    angles += angles[:1]

    # plotting the radar chart
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='skyblue', alpha=0.3)  # changed color back to skyblue
    ax.plot(angles, values, color='deepskyblue', linewidth=2)  # changed line color to deepskyblue

    # add labels
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(brands, fontsize=10, fontweight='bold', ha='right')

    # adjust brand label positions
    for label, angle in zip(ax.get_xticklabels(), angles):
        x, y = label.get_position()
        if angle == 0:
            label.set_position((x, y - 0.1))  # adjust position for the first brand
        else:
            label.set_position((x, y))  # keep positions for other brands

    # add title and grid
    plt.title('Controversy Scores of Road Bike Brands', fontsize=15, fontweight='bold', pad=20)
    ax.grid(True)

    # adjust position of the radar chart lower
    fig.subplots_adjust(top=0.7)  # adjust top margin further down

    # add total comments information
    total_comments_text = f'Total Comments: {total}'
    fig.text(0.5, 0.85, total_comments_text, ha='center', fontsize=12, fontweight='bold', color='gray')

    # add formula below the title
    plt.tight_layout()
    plt.show()
    # calculate maximum comments
    max_comments = max(data['total']) * 1.1

    # calculate controversy score
    data['controversy_score'] = (data['negative'] / data['total']) * (1 - (data['total'] / max_comments))

    # sort data by controversy score
    df_sorted = data.sort_values(by='controversy_score', ascending=True)

    # plotting the data
    plt.figure(figsize=(10, 8))

    # scatter plot
    plt.scatter(df_sorted['controversy_score'], df_sorted['brand'], color='skyblue', marker='o', s=100, alpha=0.75)
    plt.xlabel('Controversy Score', fontsize=12)
    plt.ylabel('Brand', fontsize=12)
    plt.title('Controversy Scores of Road Bike Brands', fontsize=16, fontweight='bold', pad=20)

    # add space between title and plot
    plt.title('Controversy Scores of Road Bike Brands', fontsize=16, fontweight='bold', pad=30)

    # annotate total comments
    total_comments_text = f'Total Comments: {total}'
    plt.figtext(0.55, 0.86, total_comments_text, ha='center', fontsize=12, color='gray')

    # annotate formula
    formula_text = r'$\text{Controversy Score} = \left(\frac{\text{Bad Comments}}{\text{Good Comments} + \text{Bad Comments}}\right) \times \left(1 - \frac{\text{Total Comments}}{\text{Maximum Comments}}\right)$'
    plt.figtext(0.55, 0.925, formula_text, ha='center', fontsize=12)

    # annotate maximum comments
    max_comments_text = f'Maximum Comments: {max_comments:.0f}'
    plt.figtext(0.55, 0.83, max_comments_text, ha='center', fontsize=12, color='gray')

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    RUNNABLE = True  # prevent faulty execution and data overwriting

    if RUNNABLE:   
        data = pd.read_json(r'data/sentiment_filtered.json', orient='records', lines=True)
        brand_df, sub_df, total = prep_data(data)
        # vis_one(brand_df, total)
        # vis_two(sub_df, total)
        vis_three(brand_df, total)
