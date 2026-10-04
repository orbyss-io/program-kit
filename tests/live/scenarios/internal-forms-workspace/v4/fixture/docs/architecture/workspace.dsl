workspace "Internal Forms Workspace" "Program Kit C4-aligned intake model" {
    model {
        internal_employee = person "Internal employee" "Completes governed internal forms." "ProgramKitId:internal-employee,ProgramKitType:person,ProgramKitStatus:explicit,ProgramKitOwner:Business operations"
        internal_forms_workspace = softwareSystem "Internal Forms Workspace" "Hosts the secure schema-driven forms journey." "ProgramKitId:internal-forms-workspace,ProgramKitType:software-system,ProgramKitStatus:explicit,ProgramKitOwner:Internal Forms team" {
            forms_api = container "Internal Forms API" "Owns HTTP form contracts." ".NET 10" "Api,ProgramKitId:forms-api,ProgramKitType:container,ProgramKitStatus:explicit,ProgramKitOwner:Internal Forms team"
            forms_bff = container "Internal Forms BFF" "Owns the server-managed browser session." ".NET 10" "Bff,ProgramKitId:forms-bff,ProgramKitType:container,ProgramKitStatus:explicit,ProgramKitOwner:Internal Forms team"
            forms_web = container "Internal Forms Web" "Renders immutable schema-driven forms." "React 19" "Web,ProgramKitId:forms-web,ProgramKitType:container,ProgramKitStatus:explicit,ProgramKitOwner:Internal Forms team"
        }
        forms_context = element "Internal Forms" "Bounded Context" "Owns form definition and rendering contracts." "Domain,ProgramKitId:forms-context,ProgramKitType:bounded-context,ProgramKitStatus:proposed,ProgramKitOwner:Internal Forms team"
        forms_integration = element "Forms integration" "Module / Bridge" "Composes Forms and Localization contracts." "DomainModule,ProgramKitId:forms-integration,ProgramKitType:domain-capability,ProgramKitStatus:explicit,ProgramKitOwner:Internal Forms team"
        employee_uses_web = internal_employee -> forms_web "Completes internal forms" "HTTPS" "ProgramKitId:employee-uses-web,ProgramKitStatus:explicit"
    }

    views {
        systemContext internal_forms_workspace "system-context" {
            title "Internal Forms system context"
            description "The employee and Internal Forms Workspace."
            include internal_employee internal_forms_workspace
            exclude "relationship.tag==Relationship"
            include employee_uses_web
            autolayout lr
        }
        container internal_forms_workspace "container-view" {
            title "Internal Forms containers"
            description "The accepted API, BFF, Forms, and React topology."
            include forms_api forms_bff forms_web forms_integration
            autolayout lr
        }
        custom "domain-landscape" {
            title "Internal Forms domain landscape"
            description "The core Internal Forms subdomain."
            include forms_context
            autolayout lr
        }
        custom "context-map" {
            title "Internal Forms context map"
            description "The single candidate domain boundary."
            include forms_context
            autolayout lr
        }
        custom "context-decomposition" {
            title "Internal Forms decomposition"
            description "The Forms integration module inside its context."
            include forms_context forms_integration
            autolayout lr
        }
        dynamic * "journey-complete-form" {
            title "Complete internal form"
            description "The employee opens and completes an internal form."
            1: employee_uses_web "Completes internal forms"
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
