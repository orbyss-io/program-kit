workspace "Price Calculator — provisional architecture" "Program Kit C4-aligned intake model" {
    model {
        price_calculator = softwareSystem "Price Calculator" "Organization-configurable estimation, administration and published hosted or embedded calculators." "ProgramKitId:price-calculator,ProgramKitType:software-system,ProgramKitStatus:proposed,ProgramKitOwner:consumer"
        organization_admin = person "Organization administrator" "Maintains private catalog, suppliers, forms, brands, translations and saved estimates." "ProgramKitId:organization-admin,ProgramKitType:person,ProgramKitStatus:explicit,ProgramKitOwner:consumer"
        intermediary = person "Intermediary" "Guides a consumer through an estimate; may also hold the organization administrator role." "ProgramKitId:intermediary,ProgramKitType:person,ProgramKitStatus:explicit,ProgramKitOwner:consumer"
        consumer = person "Consumer" "Receives an assisted estimate or independently submits a calculator and downloads the result." "ProgramKitId:consumer,ProgramKitType:person,ProgramKitStatus:explicit,ProgramKitOwner:consumer"
        supplier = person "Supplier" "Provides Excel data offline to the administrator in v1; has no consumer interaction." "ProgramKitId:supplier,ProgramKitType:person,ProgramKitStatus:explicit,ProgramKitOwner:consumer"
        website_publisher = person "Website publisher" "Embeds the organization's published calculator in its existing site." "ProgramKitId:website-publisher,ProgramKitType:person,ProgramKitStatus:explicit,ProgramKitOwner:consumer"
        customer_website = softwareSystem "Customer website" "Existing website displaying a published calculator; its platform is not yet specified." "ProgramKitId:customer-website,ProgramKitType:external-system,ProgramKitStatus:explicit,ProgramKitOwner:consumer"
        catalog = element "Catalog" "Bounded Context" "Provide a private, comparable, revisioned catalog of items and supplier offers." "ProgramKitId:catalog,ProgramKitType:bounded-context,ProgramKitStatus:proposed,ProgramKitOwner:consumer"
        calculator_design = element "Calculator Design" "Bounded Context" "Let organization admins publish reusable, branded estimation journeys across industries." "ProgramKitId:calculator-design,ProgramKitType:bounded-context,ProgramKitStatus:proposed,ProgramKitOwner:consumer"
        estimation = element "Estimation" "Bounded Context" "Produce understandable, historically stable budget estimates from published calculator recipes." "ProgramKitId:estimation,ProgramKitType:bounded-context,ProgramKitStatus:proposed,ProgramKitOwner:consumer"
        item_definitions = element "Item Definitions" "Module / Bridge" "Canonical item fields, three-level hierarchy, typed properties and comparable units." "ProgramKitId:item-definitions,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:catalog"
        supplier_imports = element "Supplier Imports" "Module / Bridge" "Supplier identities, supplier-code mappings, staged Excel validation and accepted offer revisions." "ProgramKitId:supplier-imports,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:catalog"
        catalog_localization = element "Catalog Localization Adapter" "Module / Bridge" "Write/import and read versioned Dutch, English, French and German item labels under catalog ownership." "ProgramKitId:catalog-localization,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:catalog"
        calculator_modeling = element "Calculator Modeling" "Module / Bridge" "Conditional selections, typed quantity rules, total-range bands and authored language content." "ProgramKitId:calculator-modeling,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:calculator-design"
        calculator_publication = element "Calculator Publication" "Module / Bridge" "Validate, preview and activate immutable coherent calculator releases referencing exact catalog and content revisions." "ProgramKitId:calculator-publication,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:calculator-design"
        organization_settings = element "Organization Publishing Settings" "Module / Bridge" "Private organization calculator identities, branding, admin grants and distribution settings." "ProgramKitId:organization-settings,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:calculator-design"
        form_mechanism = element "Forms Adapter" "Module / Bridge" "Adapt consumer branches, selections and validation to reusable form editor/runtime mechanisms." "ProgramKitId:form-mechanism,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:calculator-design"
        design_localization = element "Calculator Localization Adapter" "Module / Bridge" "Write/import translated form, brand and band text; publish and read pinned localized content." "ProgramKitId:design-localization,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:calculator-design"
        design_catalog = element "Calculator Catalog Bridge" "Module / Bridge" "Translate catalog revision lookups into authoring item references and release validation." "ProgramKitId:design-catalog,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:calculator-design"
        estimate_calculation = element "Estimate Calculation" "Module / Bridge" "Execute quantity rules, eligibility, min/max/mean, total bands and explicit completeness." "ProgramKitId:estimate-calculation,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:estimation"
        estimate_records = element "Estimate Records" "Module / Bridge" "Persist immutable answers, labels, line values, totals and revision references; authorize admin history." "ProgramKitId:estimate-records,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:estimation"
        consumer_output = element "Consumer Result Output" "Module / Bridge" "Project and export historical results without supplier identities or private offer records." "ProgramKitId:consumer-output,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:estimation"
        estimate_design = element "Estimation Recipe Bridge" "Module / Bridge" "Resolve exact published recipe, brand, four-language labels and catalog revision reference." "ProgramKitId:estimate-design,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:estimation"
        estimate_catalog = element "Estimation Catalog Bridge" "Module / Bridge" "Read exact reviewed offer revision for internal evaluation; keep supplier details server-side." "ProgramKitId:estimate-catalog,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:estimation"
        admin_uses_app = organization_admin -> price_calculator "Administrates private organization data and reviews estimates." "" "ProgramKitId:admin-uses-app,ProgramKitStatus:proposed"
        assists_in_app = intermediary -> price_calculator "Guides a consumer through a published estimate." "" "ProgramKitId:assists-in-app,ProgramKitStatus:proposed"
        consumer_uses_app = consumer -> price_calculator "Uses a public calculator and receives or downloads an estimate." "" "ProgramKitId:consumer-uses-app,ProgramKitStatus:proposed"
        publisher_uses_app = website_publisher -> price_calculator "Obtains a published calculator's embed configuration." "" "ProgramKitId:publisher-uses-app,ProgramKitStatus:proposed"
        website_embeds_app = customer_website -> price_calculator "Displays the same published calculator and its consumer results." "" "ProgramKitId:website-embeds-app,ProgramKitStatus:proposed"
        supplier_delivers_sheet = supplier -> organization_admin "Delivers Excel data offline for mapping and review." "" "ProgramKitId:supplier-delivers-sheet,ProgramKitStatus:proposed"
        admin_maintains_items = organization_admin -> catalog "Maintains item definitions, hierarchy, typed attributes and translated labels." "" "ProgramKitId:admin-maintains-items,ProgramKitStatus:proposed"
        admin_imports_offers = organization_admin -> catalog "Stages, maps, validates and accepts supplier Excel offers." "" "ProgramKitId:admin-imports-offers,ProgramKitStatus:proposed"
        admin_configures_calculator = organization_admin -> calculator_design "Configures organization calculators, brands, branches, quantities, bands and translated content." "" "ProgramKitId:admin-configures-calculator,ProgramKitStatus:proposed"
        design_reads_catalog = calculator_design -> catalog "Reads exact catalog definitions/revision for item references and release validation." "" "ProgramKitId:design-reads-catalog,ProgramKitStatus:proposed"
        admin_publishes_calculator = organization_admin -> calculator_design "Validates, previews and activates a coherent calculator release." "" "ProgramKitId:admin-publishes-calculator,ProgramKitStatus:proposed"
        estimation_reads_design = estimation -> calculator_design "Resolves a pinned execution recipe, localized text and catalog revision reference." "" "ProgramKitId:estimation-reads-design,ProgramKitStatus:proposed"
        estimation_reads_catalog = estimation -> catalog "Reads exact comparable offer revision for private server-side evaluation." "" "ProgramKitId:estimation-reads-catalog,ProgramKitStatus:proposed"
        consumer_submits_estimate = consumer -> estimation "Submits answers using the public published calculator." "" "ProgramKitId:consumer-submits-estimate,ProgramKitStatus:proposed"
        intermediary_submits_estimate = intermediary -> estimation "Submits guided answers alongside the consumer." "" "ProgramKitId:intermediary-submits-estimate,ProgramKitStatus:proposed"
        calculation_saves_snapshot = estimate_calculation -> estimate_records "Saves immutable historical inputs, outputs and revision references within Estimation." "" "ProgramKitId:calculation-saves-snapshot,ProgramKitStatus:proposed"
        estimation_shows_result = estimation -> consumer "Shows selected items, quantities, min/max, optional average, bands and incomplete status without suppliers." "" "ProgramKitId:estimation-shows-result,ProgramKitStatus:proposed"
        admin_reviews_estimate = organization_admin -> estimation "Retrieves its organization's saved estimates without recalculating them." "" "ProgramKitId:admin-reviews-estimate,ProgramKitStatus:proposed"
        consumer_downloads_pdf = consumer -> estimation "Downloads a consumer-safe historical PDF without account or email." "" "ProgramKitId:consumer-downloads-pdf,ProgramKitStatus:proposed"
        publisher_configures_website = website_publisher -> customer_website "Installs the chosen calculator embed in an existing website." "" "ProgramKitId:publisher-configures-website,ProgramKitStatus:proposed"
        admin_accepts_offers = organization_admin -> catalog "Accepts validated staged supplier offers into a new eligible catalog revision." "" "ProgramKitId:admin-accepts-offers,ProgramKitStatus:proposed"
        admin_translates_calculator = organization_admin -> calculator_design "Edits or imports four-language form, brand and classification content into a calculator draft." "" "ProgramKitId:admin-translates-calculator,ProgramKitStatus:proposed"
    }

    views {
        systemContext price_calculator "system-context" {
            title "System Context"
            include price_calculator organization_admin intermediary consumer website_publisher customer_website
            exclude "relationship.tag==Relationship"
            include admin_uses_app assists_in_app consumer_uses_app publisher_uses_app website_embeds_app
            autolayout lr
        }
        custom "domain-landscape" {
            title "Core, Supporting and Generic Responsibilities"
            include catalog calculator_design estimation item_definitions supplier_imports calculator_modeling organization_settings form_mechanism estimate_calculation consumer_output
            autolayout lr
        }
        custom "context-map" {
            title "Context Map — Explicit Read Contracts"
            include catalog calculator_design estimation
            exclude "relationship.tag==Relationship"
            include design_reads_catalog estimation_reads_design estimation_reads_catalog
            autolayout lr
        }
        dynamic * "configure-catalog-view" {
            title "Configure Item Catalog"
            1: admin_maintains_items "Maintains item definitions, hierarchy, typed attributes and translated labels."
            autolayout lr
        }
        dynamic * "import-supplier-data-view" {
            title "Import and Review Supplier Excel"
            1: supplier_delivers_sheet "Delivers Excel data offline for mapping and review."
            2: admin_imports_offers "Stages, maps, validates and accepts supplier Excel offers."
            3: admin_accepts_offers "Accepts validated staged supplier offers into a new eligible catalog revision."
            autolayout lr
        }
        dynamic * "publish-calculator-view" {
            title "Configure Translate and Publish Calculator"
            1: admin_configures_calculator "Configures organization calculators, brands, branches, quantities, bands and translated content."
            2: admin_translates_calculator "Edits or imports four-language form, brand and classification content into a calculator draft."
            3: design_reads_catalog "Reads exact catalog definitions/revision for item references and release validation."
            4: admin_publishes_calculator "Validates, previews and activates a coherent calculator release."
            autolayout lr
        }
        dynamic * "assisted-renovation-view" {
            title "Assisted Renovation Estimate"
            1: assists_in_app "Guides a consumer through a published estimate."
            2: intermediary_submits_estimate "Submits guided answers alongside the consumer."
            3: estimation_reads_design "Resolves a pinned execution recipe, localized text and catalog revision reference."
            4: estimation_reads_catalog "Reads exact comparable offer revision for private server-side evaluation."
            5: calculation_saves_snapshot "Saves immutable historical inputs, outputs and revision references within Estimation."
            6: estimation_shows_result "Shows selected items, quantities, min/max, optional average, bands and incomplete status without suppliers."
            autolayout lr
        }
        dynamic * "independent-estimate-view" {
            title "Independent Public Estimate"
            1: consumer_uses_app "Uses a public calculator and receives or downloads an estimate."
            2: consumer_submits_estimate "Submits answers using the public published calculator."
            3: estimation_reads_design "Resolves a pinned execution recipe, localized text and catalog revision reference."
            4: estimation_reads_catalog "Reads exact comparable offer revision for private server-side evaluation."
            5: calculation_saves_snapshot "Saves immutable historical inputs, outputs and revision references within Estimation."
            6: estimation_shows_result "Shows selected items, quantities, min/max, optional average, bands and incomplete status without suppliers."
            autolayout lr
        }
        dynamic * "embedded-estimate-view" {
            title "Embed Calculator and Obtain Estimate"
            1: publisher_uses_app "Obtains a published calculator's embed configuration."
            2: publisher_configures_website "Installs the chosen calculator embed in an existing website."
            3: website_embeds_app "Displays the same published calculator and its consumer results."
            4: consumer_submits_estimate "Submits answers using the public published calculator."
            5: estimation_reads_design "Resolves a pinned execution recipe, localized text and catalog revision reference."
            6: estimation_reads_catalog "Reads exact comparable offer revision for private server-side evaluation."
            7: calculation_saves_snapshot "Saves immutable historical inputs, outputs and revision references within Estimation."
            8: estimation_shows_result "Shows selected items, quantities, min/max, optional average, bands and incomplete status without suppliers."
            autolayout lr
        }
        dynamic * "review-history-view" {
            title "Review Saved Organization Estimates"
            1: admin_reviews_estimate "Retrieves its organization's saved estimates without recalculating them."
            autolayout lr
        }
        dynamic * "download-result-view" {
            title "Download Consumer Estimate PDF"
            1: consumer_downloads_pdf "Downloads a consumer-safe historical PDF without account or email."
            autolayout lr
        }
        custom "catalog-decomposition" {
            title "Catalog Modules"
            include catalog item_definitions supplier_imports catalog_localization
            autolayout lr
        }
        custom "calculator-design-decomposition" {
            title "Calculator Design Modules"
            include calculator_design calculator_modeling calculator_publication organization_settings form_mechanism design_localization design_catalog
            autolayout lr
        }
        custom "estimation-decomposition" {
            title "Estimation Modules"
            include estimation estimate_calculation estimate_records consumer_output estimate_design estimate_catalog
            exclude "relationship.tag==Relationship"
            include calculation_saves_snapshot
            autolayout lr
        }

        styles {
            element "Element" {
                shape RoundedBox
                background #F8FAFC
                color #172033
                stroke #94A3B8
                strokeWidth 2
                fontSize 22
            }
            element "Person" {
                shape Person
                background #0F766E
                color #FFFFFF
                stroke #115E59
                strokeWidth 2
            }
            element "Software System" {
                background #2563EB
                color #FFFFFF
                stroke #1D4ED8
                strokeWidth 2
            }
            element "ProgramKitType:bounded-context" {
                background #7C3AED
                color #FFFFFF
                stroke #6D28D9
                strokeWidth 2
            }
            element "ProgramKitType:domain-capability" {
                background #ECFDF5
                color #134E4A
                stroke #14B8A6
                strokeWidth 2
            }
            element "ProgramKitStatus:proposed" {
                stroke #F97316
                border dashed
            }
            relationship "Relationship" {
                color #475569
                thickness 3
                style solid
                routing Orthogonal
                fontSize 18
            }
            relationship "ProgramKitStatus:proposed" {
                color #EA580C
                style dashed
            }
        }
    }
}
