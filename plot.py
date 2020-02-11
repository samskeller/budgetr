import datetime
import matplotlib
matplotlib.use('TkAgg') # necessary for running via virtualenv on mac os x
import matplotlib.pyplot as plt
import numpy as np

def output_month_plot(month, averages, month_string):
    categories = sorted(averages.keys())
    monthly_amounts = [round(month[category]) for category in categories]
    average_amounts = [round(averages[category]) for category in categories]

    # Add a total in the left-most part of the plot
    monthly_amounts.insert(0, sum(monthly_amounts))
    average_amounts.insert(0, sum(average_amounts))
    categories.insert(0, "Totals")

    x = np.arange(len(categories))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width/2, monthly_amounts, width, label=month_string)
    rects2 = ax.bar(x + width/2, average_amounts, width, label='Average')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Amount ($)')
    ax.set_xlabel('Category')
    ax.set_title(f"Spending in {month_string} compared to average")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize="x-small")

    autolabel(rects1)
    autolabel(rects2)

    # Make room for x-axis labels
    plt.gcf().subplots_adjust(bottom=0.4)

    # Rotate category names so they don't overlap
    plt.xticks(rotation=90)

    # Make sure y-axis is high enough to accommodate tall bar labels
    tallest_bar = max(monthly_amounts + average_amounts)
    plt.ylim(0, tallest_bar + (tallest_bar / 10))

    plt.savefig(f"outputs/{month_string}.png")
