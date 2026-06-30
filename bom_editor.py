import streamlit as st
from database import db_manager


def show_bom_editor(t):
    st.markdown(f"## 🔧 {t.get('bom_editor_title', 'BOM Editor')}")
    st.caption(t.get("bom_editor_caption", "Edit Bill of Materials for each product"))

    company_id = st.session_state.get('company_id') or st.session_state.get('factory_id')
    if not company_id:
        st.warning(t.get("select_company_first", "⚠️ Please select a company first"))
        return

    products = db_manager.get_company_products(company_id)
    if not products:
        st.info(t.get("no_products", "📭 No products found"))
        return

    bom_details = db_manager.get_product_bom_details(company_id)
    bom_map = {d['product_id']: d for d in bom_details}

    product_names = {p['id']: f"{p['name_ar']} ({p['name_en']})" for p in products}
    selected_product_id = st.selectbox(
        t.get("product", "Product"),
        options=[p['id'] for p in products],
        format_func=lambda x: product_names.get(x, f"ID {x}"),
        key="bom_product_select"
    )

    if not selected_product_id:
        return

    product = next((p for p in products if p['id'] == selected_product_id), None)
    if not product:
        return

    st.markdown("---")
    st.subheader(f"📋 {product.get('name_ar', '')} ({product.get('name_en', '')})")

    current = bom_map.get(selected_product_id, {})

    with st.form("bom_edit_form"):
        col1, col2 = st.columns(2)

        with col1:
            preforms = st.number_input(t.get("bom_preforms", "Preforms per unit"),
                                       min_value=0, value=current.get('preforms_per_unit', 1) or 1, key="bom_pre")
            caps = st.number_input(t.get("bom_caps", "Caps per unit"),
                                   min_value=0, value=current.get('caps_per_unit', 1) or 1, key="bom_cap")
            labels = st.number_input(t.get("bom_labels", "Labels per unit"),
                                     min_value=0, value=current.get('labels_per_unit', 1) or 1, key="bom_lbl")

            packaging_type = st.selectbox(
                t.get("bom_packaging_type", "Packaging type"),
                options=['carton', 'shrink'],
                index=0 if current.get('packaging_type', 'carton') == 'carton' else 1,
                key="bom_pkg_type"
            )

        with col2:
            if packaging_type == 'carton':
                units_per_pkg = st.number_input(t.get("bom_units_per_carton", "Units per carton"),
                                                 min_value=1, value=current.get('units_per_carton', 48) or 48, key="bom_upc")

            units_per_pallet = st.number_input(t.get("bom_units_per_pallet", "Units per pallet"),
                                                min_value=0, value=current.get('units_per_pallet') or 0, key="bom_upp")

            shrink_film_grams = st.number_input(t.get("bom_shrink_film", "Shrink film (g/pallet)"),
                                                 min_value=0.0, value=float(current.get('shrink_film_grams_per_pallet') or 0), step=1.0, format="%.0f", key="bom_sfg")

            label_glue = st.number_input(t.get("bom_label_glue", "Label glue (g/bottle)"),
                                          min_value=0.0, value=float(current.get('label_glue_grams_per_bottle', 0.135) or 0.135), step=0.001, format="%.3f", key="bom_lg")
            carton_glue = st.number_input(t.get("bom_carton_glue", "Carton glue (g/carton)"),
                                           min_value=0.0, value=float(current.get('carton_glue_grams_per_carton', 0.5) or 0.5), step=0.1, key="bom_cg")

            if packaging_type == 'shrink':
                shrink_pieces_per_roll = st.number_input(t.get("bom_shrink_pieces_per_roll", "Shrink pieces per roll"),
                                                          min_value=0, value=current.get('shrink_pieces_per_roll', 1980) or 1980, key="bom_sppr")

        save = st.form_submit_button("💾 " + t.get("save_btn", "Save"), use_container_width=True, type="primary")

        if save:
            bom_data = dict(
                company_id=company_id,
                product_id=selected_product_id,
                preforms_per_unit=preforms,
                caps_per_unit=caps,
                labels_per_unit=labels,
                packaging_type=packaging_type,
                units_per_carton=units_per_pkg if packaging_type == 'carton' else current.get('units_per_carton', 48),
                units_per_shrink=current.get('units_per_shrink', 20),
                units_per_pallet=units_per_pallet or None,
                shrink_film_grams_per_pallet=shrink_film_grams or None,
                shrink_pieces_per_roll=shrink_pieces_per_roll if packaging_type == 'shrink' else current.get('shrink_pieces_per_roll', 1980),
                label_glue_grams_per_bottle=label_glue,
                carton_glue_grams_per_carton=carton_glue,
            )
            result = db_manager.create_product_bom_detail(**bom_data)
            if result:
                st.success(t.get("success_msg", "✅ Saved successfully"))
                st.rerun()
            else:
                st.error(t.get("save_error", "❌ Error saving BOM"))
