"""
One-off script to regenerate the three correlation-task figures used in the
report, using the app's own analytics/plotting code so they're pixel-accurate
to the live dashboard. Not part of the app itself.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dash

_dummy_app = dash.Dash(__name__, use_pages=True)

from utils.analytics.correlation import run_correlation_pipeline, load_clean_data
from pages.correlation import create_dendrogram, create_heatmap, create_time_series

OUT_DIR = os.path.join("report", "figures")
os.makedirs(OUT_DIR, exist_ok=True)

print("Running correlation pipeline...")
result = run_correlation_pipeline(n_clusters=5, linkage_method="average")

order = result["cluster_result"]["order"]

print("Building dendrogram figure...")
dendro_fig = create_dendrogram(result["cluster_result"])
dendro_fig.write_image(os.path.join(OUT_DIR, "correlation_dendrogram.png"), width=1400, height=700, scale=2)

print("Building heatmap figure...")
heatmap_fig = create_heatmap(result["clustered_matrix"], order)
heatmap_fig.write_image(os.path.join(OUT_DIR, "correlation_heatmap.png"), width=1400, height=1100, scale=2)

print("Building closing-price comparison figure (ADANIPORTS, ASIANPAINT)...")
raw_df = result["raw_df"]
ts_fig = create_time_series(raw_df, ["ADANIPORTS", "ASIANPAINT"])
ts_fig.write_image(os.path.join(OUT_DIR, "correlation_price_comparison.png"), width=1400, height=600, scale=2)

print("Done. Files written to", OUT_DIR)
