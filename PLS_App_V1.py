import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
from io import BytesIO

# Set full-width page layout
st.set_page_config(page_title="Pasture Portal PLS Calculator", layout="wide")

# Inject custom CSS for styling
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .species-area {
        background-color: #F1F8F4;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        margin-bottom: 30px;
    }
    .stButton>button {
        color: white;
        background-color: #ADC698;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Score dictionaries
soil_scores = {"Sand": 40, "Sandy Loam": 30, "Loam": 15, "Clay Loam": 10, "Clay": 5}
paddock_prep_scores = {"None": 10, "Some Prep": 30, "Full Prep": 60}
sowing_method_scores = {"Aerial": 50, "Spreader": 50, "Disk": 100, "Combine": 100}
post_planting_scores = {"Rolled": 100, "Harrowed": 50, "None": 0}
starter_fert_scores = {"Yes": 100, "No": 0}
planting_condition_scores = {
    "Good Soil Moisture": 20,
    "Friable Seed Bed": 20,
    "No Weeds/Competition": 20
}

# Functions
def calculate_field_establishment(total_score):
    return 0.05 + ((total_score - 115) / (500 - 115)) * (0.15 - 0.05)

def calculate_pls(purity, germination):
    return purity * germination

def animate_field_establishment_scale(final_field_est):
    placeholder = st.empty()
    for est in np.linspace(0.06, final_field_est, 30):
        fig, ax = plt.subplots(figsize=(5, 1), dpi=600)  # 5 inches wide, 1 inch high, 600 DPI

        cmap = plt.get_cmap('RdYlGn')
        for i in range(100):
            pos = 0.06 + (i / 100) * (0.15 - 0.06)
            ax.plot([pos], [0.5], marker='|', color=cmap(i/100), markersize=10)

        ax.plot(est, 0.6, marker='v', color='black', markersize=6)

        ax.text(0.06, 0.2, "6%\nPoor", ha='center', va='center', fontsize=6)
        ax.text(0.10, 0.2, "10%\nModerate", ha='center', va='center', fontsize=6)
        ax.text(0.15, 0.2, "15%\nExcellent", ha='center', va='center', fontsize=6)

        ax.set_xlim(0.05, 0.16)
        ax.set_ylim(0, 1)
        ax.axis('off')
        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=600, bbox_inches='tight')
        buf.seek(0)
        placeholder.image(buf, width=500)  # 500px width to match 5 inches
        plt.close(fig)
        time.sleep(0.01)

# --- Main App ---
st.title("Pasture Portal - PLS and Sowing Rate Calculator")

st.header("Site and Management Factors")
with st.expander("ℹ️ How Field Establishment is Calculated"):
    st.write("""
    Field Establishment (%) is influenced by:
    - Soil type (sand, loam, clay)
    - Paddock preparation (none, some, full)
    - Sowing method (aerial, spreader, disk, combine)
    - Post planting treatment (rolled, harrowed, none)
    - Starter fertiliser (yes/no)
    - Planting conditions (soil moisture, seedbed, competition)

    Better preparation and sowing methods lead to higher establishment rates (up to ~15%),  
    while poor conditions (heavy clay, aerial sowing, no prep) can drop it as low as 6%.
    """)

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    soil_type = st.selectbox("Select Soil Type", list(soil_scores.keys()))
with row1_col2:
    paddock_prep = st.selectbox("Select Paddock Preparation", list(paddock_prep_scores.keys()))

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    sowing_method = st.selectbox("Select Sowing Method", list(sowing_method_scores.keys()))
with row2_col2:
    post_planting = st.selectbox("Select Post Planting Treatment", list(post_planting_scores.keys()))

row3_col1, row3_col2 = st.columns(2)
with row3_col1:
    starter_fert = st.selectbox("Starter Fertiliser Used?", list(starter_fert_scores.keys()))
with row3_col2:
    planting_conditions = st.multiselect("Select Conditions at Planting", list(planting_condition_scores.keys()))

st.header("Planting Target")
total_target_plants_m2 = st.number_input("Total Desired Plants per m²", min_value=1, value=10)
grass_split = st.slider("Grass % Split", 0, 100, 70)
legume_split = 100 - grass_split

st.write(f"Grass Target Plants/m²: {total_target_plants_m2 * (grass_split/100):.2f}")
st.write(f"Legume Target Plants/m²: {total_target_plants_m2 * (legume_split/100):.2f}")

st.header("Species Input")

species_data = []
species_count = st.number_input("Number of Species to Add", min_value=1, value=2)

st.markdown('<div class="species-area">', unsafe_allow_html=True)

for i in range(species_count):
    col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 2, 2])

    with col1:
        species = st.text_input(f"Species Name {i+1}", key=f"species_{i}")
    with col2:
        germination = st.number_input(f"Germ % {i+1}", min_value=0.0, max_value=1.0, value=0.7, format="%.2f", key=f"germ_{i}")
    with col3:
        purity = st.number_input(f"Purity % {i+1}", min_value=0.0, max_value=1.0, value=0.9, format="%.2f", key=f"purity_{i}")
    with col4:
        seeds_per_kg = st.number_input(f"Seeds/kg {i+1}", min_value=1, value=300000, key=f"seeds_{i}")
    with col5:
        plant_type = st.selectbox(f"Plant Type {i+1}", ["Grass", "Legume"], key=f"type_{i}")

    species_data.append({
        "Plant Type": plant_type,
        "Species": species,
        "Germination": germination,
        "Purity": purity,
        "Seeds/kg": seeds_per_kg
    })

st.markdown('</div>', unsafe_allow_html=True)

# --- Calculate Button and Results ---
if st.button("Calculate"):
    total_score = (
        soil_scores[soil_type] +
        paddock_prep_scores[paddock_prep] +
        sowing_method_scores[sowing_method] +
        post_planting_scores[post_planting] +
        starter_fert_scores[starter_fert] +
        sum(planting_condition_scores[cond] for cond in planting_conditions)
    )
    
    field_establishment = calculate_field_establishment(total_score)

    st.header("Calculation Results")
    st.subheader(f"Calculated Field Establishment: {field_establishment*100:.2f}%")

    animate_field_establishment_scale(field_establishment)

    total_grass_plants = total_target_plants_m2 * (grass_split / 100)
    total_legume_plants = total_target_plants_m2 * (legume_split / 100)

    grass_species = [s for s in species_data if s['Plant Type'] == 'Grass']
    legume_species = [s for s in species_data if s['Plant Type'] == 'Legume']

    results = []

    for species in grass_species:
        pls = calculate_pls(species['Purity'], species['Germination'])
        viable_seeds_per_kg = species['Seeds/kg'] * pls
        target_plants_per_m2_species = total_grass_plants / len(grass_species)
        adjusted_target_plants_per_m2 = target_plants_per_m2_species / field_establishment
        sowing_rate_kg_per_m2 = adjusted_target_plants_per_m2 / viable_seeds_per_kg
        sowing_rate_kg_per_ha = sowing_rate_kg_per_m2 * 10000
        results.append({
            "Species": species['Species'],
            "Type": species['Plant Type'],
            "Sowing Rate (kg/ha)": sowing_rate_kg_per_ha
        })

    for species in legume_species:
        pls = calculate_pls(species['Purity'], species['Germination'])
        viable_seeds_per_kg = species['Seeds/kg'] * pls
        target_plants_per_m2_species = total_legume_plants / len(legume_species)
        adjusted_target_plants_per_m2 = target_plants_per_m2_species / field_establishment
        sowing_rate_kg_per_m2 = adjusted_target_plants_per_m2 / viable_seeds_per_kg
        sowing_rate_kg_per_ha = sowing_rate_kg_per_m2 * 10000
        results.append({
            "Species": species['Species'],
            "Type": species['Plant Type'],
            "Sowing Rate (kg/ha)": sowing_rate_kg_per_ha
        })

    df_results = pd.DataFrame(results)

    # --- Add Total Mix Row ---
    total_mix_rate = df_results["Sowing Rate (kg/ha)"].sum()
    total_row = {
        "Species": "🌿 Total Mix",
        "Type": "",
        "Sowing Rate (kg/ha)": total_mix_rate
    }
    df_results = pd.concat([df_results, pd.DataFrame([total_row])], ignore_index=True)

    st.subheader("Sowing Rate Results")
    st.dataframe(df_results)

    csv = df_results.to_csv(index=False).encode('utf-8')
    st.download_button("Download Results as CSV", data=csv, file_name='sowing_rates.csv', mime='text/csv')