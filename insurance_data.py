INSURANCE_CATEGORIES = {
    "HEALTH_INSURANCE": {
        "Medical_Insurance": {
            "search_term": "medical",
            "description_keywords": ["medical expenses", "illnesses", "injuries", "conditions"],
            "action_words": "covers"
        },
        "Dental_Insurance": {
            "search_term": "dental",
            "description_keywords": ["routine care", "surgeries", "treatments"],
            "action_words": "covers"
        },
        "Vision_Insurance": {
            "search_term": "vision",
            "description_keywords": ["eye exams", "glasses", "contact lenses"],
            "action_words": "covers"
        },
        "Disability_Insurance": {
            "search_term": "disability",
            "description_keywords": ["income", "disabled", "cannot work"],
            "action_words": "provides"
        },
        "Long_term_Care_Insurance": {
            "search_term": "long term",
            "description_keywords": ["long-term care services", "nursing homes"],
            "action_words": "covers"
        }
    },

    "AUTO_INSURANCE": {
        "Liability_Coverage": {
            "search_term": "liability",
            "description_keywords": ["damages", "property", "injuries", "cause"],
            "action_words": "covers"
        },
        "Collision_Coverage": {
            "search_term": "collision",
            "description_keywords": ["damage", "car", "collisions"],
            "action_words": "covers"
        },
        "Comprehensive_Coverage": {
            "search_term": "comprehensive",
            "description_keywords": ["damage", "car", "non-collision", "theft"],
            "action_words": "covers"
        },
        "Personal_Injury_Protection": {
            "search_term": "personal injury",
            "description_keywords": ["medical expenses", "passengers", "accident"],
            "action_words": "covers"
        },
        "Uninsured_Motorist_Coverage": {
            "search_term": "motorist coverage",
            "description_keywords": ["damages", "driver at fault", "insufficient insurance"],
            "action_words": "covers"
        }
    },
        "HOMEOWNERS_INSURANCE": {
        "Dwelling_Coverage": {
            "search_term": "dwelling coverage",
            "description_keywords": ["damage", "physical structure", "home"],
            "action_words": "covers"
        },
        "Personal_Property_Coverage": {
            "search_term": "personal property coverage",
            "description_keywords": ["loss", "damage", "personal belongings", "home"],
            "action_words": "covers"
        },
        "Liability_Protection": {
            "search_term": "liability protection",
            "description_keywords": ["legal costs", "injured", "property"],
            "action_words": "covers"
        },
        "Flood_Insurance": {
            "search_term": "flood",
            "description_keywords": ["damage", "flooding"],
            "action_words": "covers"
        },
        "Earthquake_Insurance": {
            "search_term": "earthquake",
            "description_keywords": ["damage", "earthquakes"],
            "action_words": "covers"
        }
    },

    "LIFE_INSURANCE": {
        "Term_Life_Insurance": {
            "search_term": "term life",
            "description_keywords": ["specific period", "10 years", "20 years"],
            "action_words": "provides"
        },
        "Whole_Life_Insurance": {
            "search_term": "whole life",
            "description_keywords": ["lifelong coverage", "savings component"],
            "action_words": "provides"
        },
        "Universal_Life_Insurance": {
            "search_term": "universal life",
            "description_keywords": ["flexible premiums", "death benefits"],
            "action_words": "provides"
        },
        "Variable_Life_Insurance": {
            "search_term": "variable life",
            "description_keywords": ["investment options", "death benefit"],
            "action_words": "provides"
        },
        "Accidental_Death_Dismemberment": {
            "search_term": ["accidental death", "dismemberment"],
            "description_keywords": ["accidental death", "injury", "dismemberment"],
            "action_words": "provides"
        }
    },

    "TRAVEL_INSURANCE": {
        "Trip_Cancellation_Insurance": {
            "search_term": "trip cancellation",
            "description_keywords": ["non-refundable", "trip costs", "cancel"],
            "action_words": "covers"
        },
        "Medical_Travel_Insurance": {
            "search_term": "medical travel",
            "description_keywords": ["medical emergencies", "traveling"],
            "action_words": "covers"
        },
        "Baggage_Insurance": {
            "search_term": "baggage",
            "description_keywords": ["loss", "damage", "luggage", "personal belongings", "travel"],
            "action_words": "covers"
        }
    },

    "PET_INSURANCE": {
        "Accident_Only_Plan": {
            "search_term": "accident only plan",
            "description_keywords": ["accidents", "illnesses", "excluding routine care"],
            "action_words": "covers"
        },
        "Comprehensive_Plan": {
            "search_term": "comprehensive plan",
            "description_keywords": ["accidents", "illnesses", "routine care"],
            "action_words": "covers"
        },
        "Wellness_Plan": {
            "search_term": "wellness plan",
            "description_keywords": ["routine veterinary care", "vaccinations", "check-ups"],
            "action_words": "covers"
        }
    },

    "BUSINESS_INSURANCE": {
        "General_Liability_Insurance": {
            "search_term": "general liability",
            "description_keywords": ["claims", "business operations"],
            "action_words": "covers"
        },
        "Professional_Liability_Insurance": {
            "search_term": "professional liability",
            "description_keywords": ["malpractice", "professional misconduct"],
            "action_words": "covers"
        },
        "Property_Insurance": {
            "search_term": "property",
            "description_keywords": ["damage", "business property"],
            "action_words": "covers"
        },
        "Commercial_Umbrella_Insurance": {
            "search_term": "commercial umbrella",
            "description_keywords": ["additional liability coverage", "underlying business insurance"],
            "action_words": "provides"
        },
        "Business_Owners_Policy": {
            "search_term": "business owners policy",
            "description_keywords": ["general liability", "property insurance", "business interruption"],
            "action_words": "combines"
        },
        "Cyber_Liability_Insurance": {
            "search_term": "cyber liability",
            "description_keywords": ["financial losses", "data breaches", "cyber events"],
            "action_words": "covers"
        },
        "Workers_Compensation_Insurance": {
            "search_term": "workers compensation",
            "description_keywords": ["benefits", "employees", "work-related injuries", "illnesses"],
            "action_words": "provides"
        },
        "Commercial_Auto_Insurance": {
            "search_term": "commercial auto",
            "description_keywords": ["vehicles", "business purposes"],
            "action_words": "covers"
        },
        "Product_Liability_Insurance": {
            "search_term": "product liability",
            "description_keywords": ["legal costs", "damages", "defective products"],
            "action_words": "covers"
        }
    },

    "SPECIALTY_INSURANCE": {
        "Event_Insurance": {
            "search_term": "event",
            "description_keywords": ["cancellations", "liabilities", "events", "weddings", "concerts"],
            "action_words": "covers"
        },
        "Boat_Insurance": {
            "search_term": "boat",
            "description_keywords": ["damages", "liabilities", "boats", "watercraft"],
            "action_words": "covers"
        },
        "Motorcycle_Insurance": {
            "search_term": "motorcycle",
            "description_keywords": ["damages", "liabilities", "motorcycles"],
            "action_words": "covers"
        },
        "Renters_Insurance": {
            "search_term": "renters",
            "description_keywords": ["personal property", "liability", "tenants"],
            "action_words": "covers"
        }
    }
}           