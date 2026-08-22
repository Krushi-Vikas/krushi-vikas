# -*- coding: utf-8 -*-
import frappe

def run():
    print("=== CREATING GOLD STANDARD BASELINE SURVEY BENCHMARK EXAMPLE ===")
    
    example_id = "BLS-EXAMPLE-001"
    if frappe.db.exists("Baseline Survey", example_id):
        try:
            doc = frappe.get_doc("Baseline Survey", example_id)
            if doc.docstatus == 1:
                doc.cancel()
            doc.delete(ignore_permissions=True)
        except Exception:
            pass
        frappe.db.commit()

    doc = frappe.get_doc({
        "doctype": "Baseline Survey",
        "name": example_id,
        "farmer_name": "Rameshwar Tukaram Jadhav",
        "contact_number": "9822334455",
        "village": "Rampur",
        "survey_date": "2026-08-22",
        "field_officer": "Administrator",
        "surveyor_name": "Anita Sharma (Lead Officer)",
        "age": 48,
        "category": "OBC",
        "house_type": "Pucca",
        "has_toilet": "Yes",
        "is_bpl": "No",
        "family_migrates": "No",
        
        # 2. Family Information & SHG (Q9-13)
        "is_shg_member": "Yes",
        "shg_name": "Jai Kisan Mahila Bachat Gat",
        "shg_has_loan": "Yes",
        "shg_business_started": "Yes",
        "shg_business_type": "Neem Oil Processing & Bio-inputs",
        
        # 3. Agricultural Details (Q14-20)
        "total_landholding_acres": 5.0,
        "irrigated_land_acres": 3.0,
        "rainfed_land_acres": 2.0,
        "conducts_soil_testing": "Yes",
        "soil_testing_last_date": "May 2025",
        "fertilizer_as_per_recommendation": "Yes",
        "yield_increase_from_soil_test": "4 Qtl.",
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
        "other_notes": "Progressive farmer adopting organic farming and drip micro-irrigation.",
        "confirmation_consent": 1,
        
        # 8. Details of Family Members (Page 1 Table 8)
        "household_members_table": [
            {"member_name": "Rameshwar Jadhav", "relation": "Self", "gender": "Male", "age": 48, "education": "Secondary [9-10]", "occupation": "Agriculture", "annual_income": 160000},
            {"member_name": "Kaushalya Jadhav", "relation": "Spouse", "gender": "Female", "age": 43, "education": "Secondary [9-10]", "occupation": "Housework", "annual_income": 40000},
            {"member_name": "Sachin Jadhav", "relation": "Son", "gender": "Male", "age": 22, "education": "Graduate", "occupation": "Salaried Job", "annual_income": 80000},
            {"member_name": "Sneha Jadhav", "relation": "Daughter", "gender": "Female", "age": 19, "education": "Higher Secondary [11-12]", "occupation": "Other", "annual_income": 0}
        ],
        
        # 4. Crop Details & Economics Table (Page 1 & 2)
        "crops_table": [
            {"season": "Kharif", "crop_name": "Cotton", "area_irrigated_acres": 2.0, "area_dryland_acres": 0.0, "yield_quintals": 18.0, "place_of_sale": "APMC Akola", "market_rate_per_qtl": 7500, "total_income": 135000, "cost_of_production": 38000, "net_profit": 97000},
            {"season": "Kharif", "crop_name": "Soybean", "area_irrigated_acres": 1.0, "area_dryland_acres": 1.0, "yield_quintals": 16.0, "place_of_sale": "APMC Akola", "market_rate_per_qtl": 4800, "total_income": 76800, "cost_of_production": 22000, "net_profit": 54800},
            {"season": "Rabi", "crop_name": "Wheat", "area_irrigated_acres": 2.0, "area_dryland_acres": 0.0, "yield_quintals": 22.0, "place_of_sale": "APMC Akola", "market_rate_per_qtl": 2900, "total_income": 63800, "cost_of_production": 18000, "net_profit": 45800},
            {"season": "Rabi", "crop_name": "Gram", "area_irrigated_acres": 0.0, "area_dryland_acres": 1.0, "yield_quintals": 8.0, "place_of_sale": "APMC Akola", "market_rate_per_qtl": 5200, "total_income": 41600, "cost_of_production": 11000, "net_profit": 30600},
            {"season": "Vegetables", "crop_name": "Tomato", "area_irrigated_acres": 0.5, "area_dryland_acres": 0.0, "yield_quintals": 25.0, "place_of_sale": "Weekly Haat", "market_rate_per_qtl": 2200, "total_income": 55000, "cost_of_production": 15000, "net_profit": 40000},
            {"season": "Horticulture (Orchards)", "crop_name": "Guava", "area_irrigated_acres": 0.5, "area_dryland_acres": 0.0, "yield_quintals": 20.0, "place_of_sale": "Local Trader", "market_rate_per_qtl": 3000, "total_income": 60000, "cost_of_production": 14000, "net_profit": 46000}
        ],
        
        # 21. Irrigation Sources (Page 2 Table 1)
        "irrigation_sources_table": [
            {"source_name": "Open Well", "quantity": 1, "depth_feet": 48.0, "water_availability_months": 10},
            {"source_name": "Borewell", "quantity": 1, "depth_feet": 200.0, "water_availability_months": 12},
            {"source_name": "Other", "quantity": 1, "depth_feet": 12.0, "water_availability_months": 8}
        ],
        
        # 21. Irrigation Equipment (Page 2 Table 2)
        "irrigation_equipment_table": [
            {"equipment_name": "Electric Pump", "quantity_and_capacity": "1 unit (5 HP)"},
            {"equipment_name": "Solar Pump", "quantity_and_capacity": "1 unit (3 HP)"},
            {"equipment_name": "Submersible Pump", "quantity_and_capacity": "1 unit (5 HP)"}
        ],
        
        # 24. Farm Conservation Works (Page 2 Table 24)
        "farm_conservation_works_table": [
            {"structure_type": "Farm Bunding (Shet Bandh Bandisti)", "status": "Yes", "length_or_count": "550 m", "implementing_dept": "Agriculture Dept", "is_maintained": "Yes"},
            {"structure_type": "Farm Pond (Shet Tale)", "status": "Yes", "length_or_count": "30x30 m", "implementing_dept": "Govt Scheme", "is_maintained": "Yes"},
            {"structure_type": "Continuous Contour Trenches (CCT)", "status": "Yes", "length_or_count": "300 m", "implementing_dept": "Watershed Mission", "is_maintained": "Yes"},
            {"structure_type": "Water Absorption Trenches (WAT)", "status": "Yes", "length_or_count": "150 m", "implementing_dept": "Watershed Mission", "is_maintained": "Yes"}
        ],
        
        # 30. Stream / Nala Conservation Structures (Page 2 Table 30)
        "nullah_conservation_structures_table": [
            {"structure_name": "Cement Nala Bund (CNB)", "count": 2, "dimensions": "20m x 3.0m", "scheme_name": "Jalyukt Shivar", "is_maintained": "Yes"},
            {"structure_name": "Gabion Structure", "count": 2, "dimensions": "12m x 1.5m", "scheme_name": "Watershed Dev", "is_maintained": "Yes"},
            {"structure_name": "Recharge Shaft", "count": 1, "dimensions": "3m x 10m", "scheme_name": "Groundwater Dept", "is_maintained": "Yes"},
            {"structure_name": "Nala Deepening / Widening", "count": 1, "dimensions": "500 m", "scheme_name": "Galmukt Shivar", "is_maintained": "Yes"}
        ],
        
        # 50. Livestock Details (Page 3 Table 50)
        "livestock_table": [
            {"livestock_type": "Cow", "count": 2, "daily_milk_production_liters": 16.0, "domestic_use_liters": 2.0, "sale_liters": 14.0, "income_generated": 75600},
            {"livestock_type": "Buffalo", "count": 1, "daily_milk_production_liters": 9.0, "domestic_use_liters": 1.0, "sale_liters": 8.0, "income_generated": 50400},
            {"livestock_type": "Bullock", "count": 2, "daily_milk_production_liters": 0, "domestic_use_liters": 0, "sale_liters": 0, "income_generated": 0},
            {"livestock_type": "Goat / Sheep", "count": 6, "daily_milk_production_liters": 0, "domestic_use_liters": 0, "sale_liters": 0, "income_generated": 24000},
            {"livestock_type": "Poultry / Hen", "count": 20, "daily_milk_production_liters": 0, "domestic_use_liters": 0, "sale_liters": 0, "income_generated": 28000}
        ],
        
        # 53. Details of Assets Owned (Page 3 Table 53)
        "family_assets_table": [
            {"asset_description": "House", "quantity": 1, "estimated_value": 650000},
            {"asset_description": "Television (TV)", "quantity": 1, "estimated_value": 22000},
            {"asset_description": "Smartphone", "quantity": 3, "estimated_value": 36000},
            {"asset_description": "Refrigerator", "quantity": 1, "estimated_value": 18000},
            {"asset_description": "Two-Wheeler (Bike/Scooter)", "quantity": 2, "estimated_value": 110000},
            {"asset_description": "Four-Wheeler (Car/Jeep)", "quantity": 1, "estimated_value": 320000},
            {"asset_description": "Bullock Cart", "quantity": 1, "estimated_value": 28000},
            {"asset_description": "Tractor", "quantity": 1, "estimated_value": 550000},
            {"asset_description": "Biogas Unit", "quantity": 1, "estimated_value": 35000},
            {"asset_description": "LPG Gas Connection", "quantity": 1, "estimated_value": 4500},
            {"asset_description": "Other Farm Implements", "quantity": 3, "estimated_value": 42000}
        ],
        
        # 54. Loan / Debt Details (Page 3 Table 54)
        "loans_table": [
            {"loan_category": "Crop Loan (KCC)", "loan_amount": 150000, "current_outstanding": 120000, "bank_name": "State Bank of India"},
            {"loan_category": "Agri-Allied Loan", "loan_amount": 60000, "current_outstanding": 0, "bank_name": "DCC Bank Akola"},
            {"loan_category": "Business / Commercial Loan", "loan_amount": 40000, "current_outstanding": 25000, "bank_name": "Bank of Maharashtra"}
        ],
        
        # Family Income Breakdown (Page 4)
        "family_income_table": [
            {"income_source": "Agriculture / Farming", "monthly_amount": 26200.00, "annual_amount": 314400},
            {"income_source": "Allied Business / Other", "monthly_amount": 14833.33, "annual_amount": 178000},
            {"income_source": "Salaried Job / Service", "monthly_amount": 6666.67, "annual_amount": 80000},
            {"income_source": "Business / Trade", "monthly_amount": 3333.33, "annual_amount": 40000}
        ],
        
        # Family Expenditure Breakdown (Page 4)
        "family_expenditure_table": [
            {"expenditure_category": "Agriculture Operations", "monthly_amount": 9833.33, "annual_amount": 118000},
            {"expenditure_category": "Livestock & Fodder", "monthly_amount": 2500.00, "annual_amount": 30000},
            {"expenditure_category": "Education & Schooling", "monthly_amount": 3500.00, "annual_amount": 42000},
            {"expenditure_category": "Groceries & Household Expenses", "monthly_amount": 7500.00, "annual_amount": 90000},
            {"expenditure_category": "Allied Business Expenses", "monthly_amount": 1200.00, "annual_amount": 14400}
        ]
    })
    
    doc.insert(ignore_permissions=True)
    doc.submit()
    frappe.db.commit()
    print(f"Created and Submitted Benchmark Example Record: {doc.name} for {doc.farmer_name}")
