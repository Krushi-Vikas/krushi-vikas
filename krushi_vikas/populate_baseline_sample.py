# -*- coding: utf-8 -*-
import frappe

def run():
    print("=== POPULATING BASELINE SURVEY WITH ALL PDF CHILD TABLES & COLUMNS ===")
    
    # 1. Clean existing baseline survey documents
    for docname in frappe.get_all("Baseline Survey", pluck="name"):
        try:
            doc = frappe.get_doc("Baseline Survey", docname)
            if doc.docstatus == 1:
                doc.cancel()
            doc.delete(ignore_permissions=True)
            print(f"Deleted old baseline doc: {docname}")
        except Exception as e:
            print(f"Note deleting {docname}: {e}")

    frappe.db.commit()

    # 2. Baseline Survey 1: Ramesh Tukaram Patil (Kalyanpur)
    doc1 = frappe.get_doc({
        "doctype": "Baseline Survey",
        "farmer_name": "Ramesh Tukaram Patil",
        "contact_number": "9823456789",
        "village": "Kalyanpur",
        "survey_date": "2026-08-20",
        "field_officer": "Administrator",
        "surveyor_name": "Anita Sharma (Lead Officer)",
        "age": 46,
        "category": "OBC",
        "house_type": "Pucca",
        "has_toilet": "Yes",
        "is_bpl": "No",
        "family_migrates": "No",
        
        # 2. Family Information & SHG (Q9-13)
        "is_shg_member": "Yes",
        "shg_name": "Krushi Kranti Mahila Bachat Gat",
        "shg_has_loan": "Yes",
        "shg_business_started": "Yes",
        "shg_business_type": "Organic Compost Unit",
        
        # 3. Agricultural Details (Q14-20)
        "total_landholding_acres": 4.5,
        "irrigated_land_acres": 2.5,
        "rainfed_land_acres": 2.0,
        "conducts_soil_testing": "Yes",
        "soil_testing_last_date": "May 2025",
        "fertilizer_as_per_recommendation": "Yes",
        "yield_increase_from_soil_test": "2 Qtl.",
        "produce_sorted_graded": "Yes",
        "tech_info_source": "KVK",
        "practices_organic_farming": "Yes",
        
        # 5. Irrigation & Water Conservation Structures (Q22-30)
        "aware_govt_water_schemes": "Yes",
        "availed_water_scheme_benefits": "Yes",
        "participates_in_gpdp_water": "Yes",
        "nature_of_gpdp_participation": "Suggesting works",
        "village_water_awareness_programs": "Yes",
        "has_stream_near_land": "Yes",
        "stream_structures_constructed": "Yes",
        
        # 6. Drinking Water Details & Water Security Plan (Q31-48)
        "has_village_water_committee": "Yes",
        "participates_drinking_water_mgmt": "Yes",
        "drinking_water_source": "Tap Water",
        "drinking_water_ownership": "Public",
        "functional_tap_scheme": "Yes",
        "scheme_regular_om": "Yes",
        "drinking_water_at_home": "Yes",
        "water_supply_days_week": "Daily",
        "water_supply_duration": "1 Hr+",
        "drinking_water_year_round": "Yes",
        "scarcity_water_mgmt": "Private Borewell",
        "drinking_water_distance": "At Home",
        "wsp_awareness": "Yes",
        "wsp_info_source": "KVK",
        "wsp_drafting_participation": "Yes",
        "wsp_implemented_scarcity": "Yes",
        "water_budgeting_practices": "Drip Irrigation",
        
        # 7. Livestock Details (Q49, 51, 52)
        "owns_livestock": "Yes",
        "cattle_shed_type": "Pucca",
        "milk_sale_channel": "Dairy",
        
        # 10. Additional Remarks & Declaration
        "other_notes": "Progressive farmer with strong community leadership.",
        "confirmation_consent": 1,
        
        # 8. Details of Family Members (Page 1 Table 8)
        "household_members_table": [
            {"member_name": "Ramesh Patil", "relation": "Self", "gender": "Male", "age": 46, "education": "Secondary [9-10]", "occupation": "Agriculture", "annual_income": 140000},
            {"member_name": "Savitri Patil", "relation": "Spouse", "gender": "Female", "age": 41, "education": "Middle [5-8]", "occupation": "Housework", "annual_income": 36000},
            {"member_name": "Ganesh Patil", "relation": "Son", "gender": "Male", "age": 20, "education": "Higher Secondary [11-12]", "occupation": "Other", "annual_income": 0},
            {"member_name": "Pooja Patil", "relation": "Daughter", "gender": "Female", "age": 17, "education": "Secondary [9-10]", "occupation": "Other", "annual_income": 0}
        ],
        
        # 4. Crop Details & Economics Table (Page 1 & 2)
        "crops_table": [
            {"season": "Kharif", "crop_name": "Soybean", "area_irrigated_acres": 1.5, "area_dryland_acres": 1.0, "yield_quintals": 18.0, "place_of_sale": "APMC Akola", "market_rate_per_qtl": 4600, "total_income": 82800, "cost_of_production": 24000, "net_profit": 58800},
            {"season": "Kharif", "crop_name": "Cotton", "area_irrigated_acres": 1.0, "area_dryland_acres": 1.0, "yield_quintals": 14.0, "place_of_sale": "Local Ginning", "market_rate_per_qtl": 7200, "total_income": 100800, "cost_of_production": 32000, "net_profit": 68800},
            {"season": "Rabi", "crop_name": "Wheat", "area_irrigated_acres": 1.5, "area_dryland_acres": 0.0, "yield_quintals": 16.0, "place_of_sale": "APMC Akola", "market_rate_per_qtl": 2800, "total_income": 44800, "cost_of_production": 14000, "net_profit": 30800},
            {"season": "Vegetables", "crop_name": "Tomato & Chilli", "area_irrigated_acres": 0.5, "area_dryland_acres": 0.0, "yield_quintals": 22.0, "place_of_sale": "Village Haat", "market_rate_per_qtl": 2000, "total_income": 44000, "cost_of_production": 12000, "net_profit": 32000}
        ],
        
        # 21. Irrigation Sources (Page 2 Table 1)
        "irrigation_sources_table": [
            {"source_name": "Open Well", "quantity": 1, "depth_feet": 45.0, "water_availability_months": 9},
            {"source_name": "Borewell", "quantity": 1, "depth_feet": 180.0, "water_availability_months": 11}
        ],
        
        # 21. Irrigation Equipment (Page 2 Table 2)
        "irrigation_equipment_table": [
            {"equipment_name": "Electric Pump", "quantity_and_capacity": "1 unit (5 HP)"},
            {"equipment_name": "Submersible Pump", "quantity_and_capacity": "1 unit (3 HP)"}
        ],
        
        # 24. Farm Conservation Works (Page 2 Table 24)
        "farm_conservation_works_table": [
            {"structure_type": "Farm Bunding (Shet Bandh Bandisti)", "status": "Yes", "length_or_count": "450 m", "implementing_dept": "Agriculture Dept", "is_maintained": "Yes"},
            {"structure_type": "Farm Pond (Shet Tale)", "status": "Yes", "length_or_count": "30x30 m", "implementing_dept": "Govt Scheme", "is_maintained": "Yes"},
            {"structure_type": "Continuous Contour Trenches (CCT)", "status": "Yes", "length_or_count": "200 m", "implementing_dept": "NGO Project", "is_maintained": "Yes"}
        ],
        
        # 30. Stream / Nala Conservation Structures (Page 2 Table 30)
        "nullah_conservation_structures_table": [
            {"structure_name": "Cement Nala Bund (CNB)", "count": 1, "dimensions": "18m x 2.5m", "scheme_name": "Jalyukt Shivar", "is_maintained": "Yes"},
            {"structure_name": "Gabion Structure", "count": 2, "dimensions": "10m x 1.5m", "scheme_name": "Watershed Dev", "is_maintained": "Yes"},
            {"structure_name": "Nala Deepening / Widening", "count": 1, "dimensions": "300 m", "scheme_name": "Galmukt Shivar", "is_maintained": "Yes"}
        ],
        
        # 50. Livestock Details (Page 3 Table 50)
        "livestock_table": [
            {"livestock_type": "Cow", "count": 2, "daily_milk_production_liters": 12.0, "domestic_use_liters": 2.0, "sale_liters": 10.0, "income_generated": 54000},
            {"livestock_type": "Bullock", "count": 2, "daily_milk_production_liters": 0, "domestic_use_liters": 0, "sale_liters": 0, "income_generated": 0},
            {"livestock_type": "Goat / Sheep", "count": 4, "daily_milk_production_liters": 0, "domestic_use_liters": 0, "sale_liters": 0, "income_generated": 16000}
        ],
        
        # 53. Details of Assets Owned (Page 3 Table 53)
        "family_assets_table": [
            {"asset_description": "House", "quantity": 1, "estimated_value": 450000},
            {"asset_description": "Television (TV)", "quantity": 1, "estimated_value": 15000},
            {"asset_description": "Smartphone", "quantity": 2, "estimated_value": 24000},
            {"asset_description": "Refrigerator", "quantity": 1, "estimated_value": 14000},
            {"asset_description": "Two-Wheeler (Bike/Scooter)", "quantity": 1, "estimated_value": 65000},
            {"asset_description": "Bullock Cart", "quantity": 1, "estimated_value": 25000},
            {"asset_description": "LPG Gas Connection", "quantity": 1, "estimated_value": 4000},
            {"asset_description": "Other Farm Implements", "quantity": 2, "estimated_value": 22000}
        ],
        
        # 54. Loan / Debt Details (Page 3 Table 54)
        "loans_table": [
            {"loan_category": "Crop Loan (KCC)", "loan_amount": 120000, "current_outstanding": 90000, "bank_name": "State Bank of India"},
            {"loan_category": "Agri-Allied Loan", "loan_amount": 40000, "current_outstanding": 0, "bank_name": "DCC Bank"}
        ],
        
        # Family Income Breakdown (Page 4)
        "family_income_table": [
            {"income_source": "Agriculture / Farming", "monthly_amount": 15866.67, "annual_amount": 190400},
            {"income_source": "Allied Business / Other", "monthly_amount": 5833.33, "annual_amount": 70000},
            {"income_source": "Business / Trade", "monthly_amount": 2500.00, "annual_amount": 30000}
        ],
        
        # Family Expenditure Breakdown (Page 4)
        "family_expenditure_table": [
            {"expenditure_category": "Agriculture Operations", "monthly_amount": 6833.33, "annual_amount": 82000},
            {"expenditure_category": "Livestock & Fodder", "monthly_amount": 1500.00, "annual_amount": 18000},
            {"expenditure_category": "Education & Schooling", "monthly_amount": 2500.00, "annual_amount": 30000},
            {"expenditure_category": "Groceries & Household Expenses", "monthly_amount": 6000.00, "annual_amount": 72000}
        ]
    })
    doc1.insert(ignore_permissions=True)
    doc1.submit()
    print(f"Created & Submitted Baseline Survey 1: {doc1.name} (Farmer: {doc1.farmer_name})")

    # 3. Baseline Survey 2: Sunita Rahul Shinde (Sonapur)
    doc2 = frappe.get_doc({
        "doctype": "Baseline Survey",
        "farmer_name": "Sunita Rahul Shinde",
        "contact_number": "9765432101",
        "village": "Sonapur",
        "survey_date": "2026-08-21",
        "field_officer": "Administrator",
        "surveyor_name": "Anita Sharma (Lead Officer)",
        "age": 38,
        "category": "SC",
        "house_type": "Semi-Pucca",
        "has_toilet": "Yes",
        "is_bpl": "Yes",
        "family_migrates": "No",
        
        # 2. Family Information & SHG (Q9-13)
        "is_shg_member": "Yes",
        "shg_name": "Savitribai Phule Bachat Gat",
        "shg_has_loan": "Yes",
        "shg_business_started": "Yes",
        "shg_business_type": "Poultry & Kitchen Garden",
        
        # 3. Agricultural Details (Q14-20)
        "total_landholding_acres": 3.0,
        "irrigated_land_acres": 1.5,
        "rainfed_land_acres": 1.5,
        "conducts_soil_testing": "Yes",
        "soil_testing_last_date": "April 2025",
        "fertilizer_as_per_recommendation": "Yes",
        "yield_increase_from_soil_test": "1 Qtl.",
        "produce_sorted_graded": "Yes",
        "tech_info_source": "NGO-Institute",
        "practices_organic_farming": "Yes",
        
        # 5. Irrigation & Water Conservation Structures (Q22-30)
        "aware_govt_water_schemes": "Yes",
        "availed_water_scheme_benefits": "Yes",
        "participates_in_gpdp_water": "Yes",
        "nature_of_gpdp_participation": "Scheme implementation",
        "village_water_awareness_programs": "Yes",
        "has_stream_near_land": "No",
        "stream_structures_constructed": "No",
        
        # 6. Drinking Water Details & Water Security Plan (Q31-48)
        "has_village_water_committee": "Yes",
        "participates_drinking_water_mgmt": "Yes",
        "drinking_water_source": "Tap Water",
        "drinking_water_ownership": "Public",
        "functional_tap_scheme": "Yes",
        "scheme_regular_om": "Yes",
        "drinking_water_at_home": "Yes",
        "water_supply_days_week": "Daily",
        "water_supply_duration": "45 min",
        "drinking_water_year_round": "Yes",
        "scarcity_water_mgmt": "Handpump",
        "drinking_water_distance": "At Home",
        "wsp_awareness": "Partially",
        "wsp_info_source": "NGO-Institution",
        "wsp_drafting_participation": "Yes",
        "wsp_implemented_scarcity": "Yes",
        "water_budgeting_practices": "Rainwater Harvesting",
        
        # 7. Livestock Details (Q49, 51, 52)
        "owns_livestock": "Yes",
        "cattle_shed_type": "Kutcha",
        "milk_sale_channel": "Dairy",
        
        # 10. Additional Remarks & Declaration
        "other_notes": "Active SHG secretary managing group poultry and organic vegetable plot.",
        "confirmation_consent": 1,
        
        # 8. Details of Family Members (Page 1 Table 8)
        "household_members_table": [
            {"member_name": "Sunita Shinde", "relation": "Self", "gender": "Female", "age": 38, "education": "Secondary [9-10]", "occupation": "Agriculture", "annual_income": 95000},
            {"member_name": "Rahul Shinde", "relation": "Spouse", "gender": "Male", "age": 42, "education": "Secondary [9-10]", "occupation": "Agriculture", "annual_income": 110000},
            {"member_name": "Prathamesh Shinde", "relation": "Son", "gender": "Male", "age": 16, "education": "Secondary [9-10]", "occupation": "Other", "annual_income": 0}
        ],
        
        # 4. Crop Details & Economics Table (Page 1 & 2)
        "crops_table": [
            {"season": "Kharif", "crop_name": "Cotton", "area_irrigated_acres": 1.0, "area_dryland_acres": 0.5, "yield_quintals": 12.0, "place_of_sale": "Local APMC", "market_rate_per_qtl": 7100, "total_income": 85200, "cost_of_production": 28000, "net_profit": 57200},
            {"season": "Rabi", "crop_name": "Gram (Chickpea)", "area_irrigated_acres": 0.5, "area_dryland_acres": 1.0, "yield_quintals": 8.0, "place_of_sale": "Local APMC", "market_rate_per_qtl": 5000, "total_income": 40000, "cost_of_production": 12000, "net_profit": 28000}
        ],
        
        # 21. Irrigation Sources (Page 2 Table 1)
        "irrigation_sources_table": [
            {"source_name": "Open Well", "quantity": 1, "depth_feet": 50.0, "water_availability_months": 8}
        ],
        
        # 21. Irrigation Equipment (Page 2 Table 2)
        "irrigation_equipment_table": [
            {"equipment_name": "Electric Pump", "quantity_and_capacity": "1 unit (3 HP)"}
        ],
        
        # 24. Farm Conservation Works (Page 2 Table 24)
        "farm_conservation_works_table": [
            {"structure_type": "Farm Bunding (Shet Bandh Bandisti)", "status": "Yes", "length_or_count": "250 m", "implementing_dept": "PMKSY", "is_maintained": "Yes"}
        ],
        
        # 50. Livestock Details (Page 3 Table 50)
        "livestock_table": [
            {"livestock_type": "Cow", "count": 1, "daily_milk_production_liters": 7.0, "domestic_use_liters": 1.5, "sale_liters": 5.5, "income_generated": 30000},
            {"livestock_type": "Poultry / Hen", "count": 15, "daily_milk_production_liters": 0, "domestic_use_liters": 0, "sale_liters": 0, "income_generated": 22000}
        ],
        
        # 53. Details of Assets Owned (Page 3 Table 53)
        "family_assets_table": [
            {"asset_description": "House", "quantity": 1, "estimated_value": 250000},
            {"asset_description": "Smartphone", "quantity": 2, "estimated_value": 20000},
            {"asset_description": "Two-Wheeler (Bike/Scooter)", "quantity": 1, "estimated_value": 45000},
            {"asset_description": "LPG Gas Connection", "quantity": 1, "estimated_value": 3500}
        ],
        
        # 54. Loan / Debt Details (Page 3 Table 54)
        "loans_table": [
            {"loan_category": "Crop Loan (KCC)", "loan_amount": 60000, "current_outstanding": 45000, "bank_name": "Bank of Maharashtra"}
        ],
        
        # Family Income Breakdown (Page 4)
        "family_income_table": [
            {"income_source": "Agriculture / Farming", "monthly_amount": 10433.33, "annual_amount": 125200},
            {"income_source": "Allied Business / Other", "monthly_amount": 4333.33, "annual_amount": 52000}
        ],
        
        # Family Expenditure Breakdown (Page 4)
        "family_expenditure_table": [
            {"expenditure_category": "Agriculture Operations", "monthly_amount": 3333.33, "annual_amount": 40000},
            {"expenditure_category": "Groceries & Household Expenses", "monthly_amount": 4500.00, "annual_amount": 54000}
        ]
    })
    doc2.insert(ignore_permissions=True)
    doc2.submit()
    print(f"Created & Submitted Baseline Survey 2: {doc2.name} (Farmer: {doc2.farmer_name})")

    frappe.db.commit()
    print("=== BASELINE SURVEY COMPLETE SAMPLE POPULATION SUCCESSFUL! ===")
