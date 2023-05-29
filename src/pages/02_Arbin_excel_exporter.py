import os
import pathlib
import tempfile

import streamlit as st
import cellpy


st.title("Arbin Excel Exporter :sunglasses:")
st.write("By Jan Petter Maehlen, IFE")


# --- Settings ---
settings = st.expander("Cell information", expanded=True)
cycles = st.checkbox("Export voltage-curves", value=False)
raw = st.checkbox("Export raw-data", value=False)
st.write(":warning: Exporting raw-data and/or cycles might take several minutes to perform.")
nom_cap_specifics = settings.selectbox("Specific: ", ["gravimetric", "areal"])
cycle_mode = settings.selectbox("Cycle mode:", ["standard", "anode",], help="select anode if you are testing anode in half-cell configuration")
mass = settings.number_input("Mass (mg):", min_value=0.0001, max_value=5000.0, value=1.0)
nominal_capacity = settings.number_input(
    "Nominal capacity (mAh/g):", min_value=10.0, max_value=5000.0, value=372.0
)

area = settings.number_input("Area (cm2):", min_value=0.0001, max_value=5000.0, value=1.0)

# TODO: add option for selecting other file types (cellpy-files and .h5 from arbin5)
raw_file_type = "arbin_res"
raw_file_extension = "res"

summary_kwargs = {"nom_cap_specifics": "gravimetric"}

# --- Upload file ---
raw_file = st.file_uploader(f"Upload raw file (*.{raw_file_extension})", type=[raw_file_extension])
button = st.button("Process file")

st.divider()

# --- Process file ---
if raw_file is not None and button:
    progress_bar = st.progress(0.0, "Reading file ...")
    raw_bytes = raw_file.read()

    progress_bar.progress(0.1, "Reading file ...")
    raw_file_name = raw_file.name
    temporary_directory = pathlib.Path(tempfile.gettempdir())
    tmp_raw_file = temporary_directory / raw_file_name
    tmp_xlsx_file = tmp_raw_file.with_suffix(".xlsx")

    with open(tmp_raw_file, "wb") as f:
        f.write(raw_bytes)

    summary_kwargs["nom_cap_specifics"] = nom_cap_specifics

    progress_bar.progress(0.3, "Reading and processing file ...")

    # TODO: split this up into two steps (read and make summary)
    c = cellpy.get(
        tmp_raw_file,
        instrument=raw_file_type,
        mass=mass,
        area=area,
        cycle_mode=cycle_mode,
        nominal_capacity=nominal_capacity,
        summary_kwargs = summary_kwargs,
        refuse_copying=True,
    )

    if cycles:
        progress_bar.progress(0.5, "Extracting cycles and converting ...")
    else:
        progress_bar.progress(0.5, "Converting ...")
    c.to_excel(tmp_xlsx_file, raw=raw, cycles=cycles)

    progress_bar.progress(0.9, "Wrapping up ...")
    with open(tmp_xlsx_file, "rb") as f:
        tmp_xlsx_bytes = f.read()

    progress_bar.progress(1.0, "Done!")

    st.write("Download file:")
    st.download_button(
        label="Download",
        data=tmp_xlsx_bytes,
        file_name=tmp_xlsx_file.name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
