import streamlit as st
import pandas as pd

import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

# Function to calculate potential savings
def calculate_savings(current_ratios, costs, max_variances):
    savings = []
    valid_ratios_a = []
    ratio_a_min = max(0, current_ratios[0] - max_variances[0])
    ratio_a_max = min(100, current_ratios[0] + max_variances[0])
    ratios = np.linspace(ratio_a_min, ratio_a_max, int(ratio_a_max - ratio_a_min) + 1)  # Ratios in percentage
    current_weighted_cost = sum(r / 100 * c for r, c in zip(current_ratios, costs))
    for ratio_a in ratios:
        ratio_b = 100 - ratio_a
        if ratio_b < max(0, current_ratios[1] - max_variances[1]) or ratio_b > min(100, current_ratios[1] + max_variances[1]):
            continue
        weighted_cost = (ratio_a / 100) * costs[0] + (ratio_b / 100) * costs[1]
        saving = (current_weighted_cost - weighted_cost) / current_weighted_cost * 100
        if saving > 0:  # Only consider positive savings
            savings.append(saving)
            valid_ratios_a.append(ratio_a)
    return valid_ratios_a, savings

# Main content
st.write("## Ingredient Ratios and Costs")

# Initial data for the data editor
initial_data = {
    "Ingredient": ["ingredient_1", "ingredient_2"],
    "Ratio (%)": [65, 35],
    "Cost per Pound": [0.12, 0.39],
    "Max Variance (%)": [20, 20]
}

ingredient_df = pd.DataFrame(initial_data)

# Use st.data_editor to allow dynamic row addition
ingredient_df = st.data_editor(
    ingredient_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Ratio (%)": st.column_config.NumberColumn(
            "Ratio (%)",
            min_value=0,
            max_value=100,
            step=1,
            format="%d%%"
        ),
        "Cost per Pound": st.column_config.NumberColumn(
            "Cost per Pound ($)",
            format="$ %.2f"
        ),
        "Max Variance (%)": st.column_config.NumberColumn(
            "Max Variance (%)",
            min_value=0,
            max_value=100,
            step=1,
            format="%d%%"
        )
    }
)

# Check if the entered percentages add up to 100
if ingredient_df["Ratio (%)"].sum() != 100:
    st.error("The total of the 'Ratio (%)' column must add up to 100.")
else:
    total_pounds = st.number_input("Total pounds (optional):", min_value=0.0, value=1.0)
    total_spend = st.number_input("Total current spend (optional):", min_value=0.0, value=100.0)

    # Calculate potential savings
    ratios, savings = calculate_savings(ingredient_df["Ratio (%)"], ingredient_df["Cost per Pound"], ingredient_df["Max Variance (%)"])

    # Ensure all arrays are of the same length
    if len(ratios) == len(savings):
        # Create a DataFrame for Plotly
        plot_data = pd.DataFrame({
            "Ratio of Ingredient A (%)": ratios,
            "Ratio of Ingredient B (%)": [100 - r for r in ratios],
            "Potential Savings (%)": savings
        })

        # Determine color based on savings
        def get_color(saving):
            if saving > 5:
                return 'green'
            elif saving < -5:
                return 'red'
            else:
                return 'yellow'

        plot_data['Color'] = plot_data['Potential Savings (%)'].apply(get_color)

        # Manually specify colors
        color_discrete_map = {
            'green': 'green',
            'red': 'red',
            'yellow': 'yellow'
        }

        # Plot potential savings using Plotly
        fig = px.scatter(
            plot_data,
            x="Ratio of Ingredient A (%)",
            y="Potential Savings (%)",
            color="Color",
            color_discrete_map=color_discrete_map,
            hover_data={
                "Ratio of Ingredient A (%)": True,
                "Ratio of Ingredient B (%)": True,
                "Potential Savings (%)": True,
                "Color": False
            },
            labels={
                "Ratio of Ingredient A (%)": "Percentage of Ingredient A",
                "Potential Savings (%)": "Potential Savings (%)"
            },
            title="Potential Savings Based on Ingredient Ratios"
        )

        # Plot current weighted cost as a blue dot
        current_weighted_cost = sum(r / 100 * c for r, c in zip(ingredient_df["Ratio (%)"], ingredient_df["Cost per Pound"]))
        current_ratio_a = ingredient_df["Ratio (%)"][0]
        current_saving = (current_weighted_cost - current_weighted_cost) / current_weighted_cost * 100
        fig.add_scatter(x=[current_ratio_a], y=[current_saving], mode='markers', marker=dict(color='blue', size=10), name='Current Cost')

        st.plotly_chart(fig)

        # Surface a dataframe with the ratios, weighted cost per pound, and projected savings
        plot_data = plot_data[plot_data["Potential Savings (%)"] > 0]  # Filter for positive savings
        plot_data = plot_data.sort_values(by="Potential Savings (%)", ascending=False)  # Sort by savings

        st.write("### Detailed Savings Data")
        st.dataframe(plot_data)

    else:
        st.error("Error: Mismatch in lengths of calculated ratios and savings.")
