install.packages("readxl")
install.packages("shiny")
install.packages("dplyr")
install.packages("ggplot2")
install.packages("ggrepel")
install.packages("scales")
library(shiny)
library(readxl)
library(dplyr)
library(ggplot2)
library(ggrepel)
library(scales)

# ── Load data ──────────────────────────────────────────────────────────────────
# Replace the path below with your actual Excel file path
df <- read_excel("CAMS_1 copy.xlsx")

# Sample data for testing — remove this block once you load your real file


# ── UI ────────────────────────────────────────────────────────────────────────
ui <- fluidPage(
  tags$head(tags$style(HTML("
    body {
      background-color: #f4f6f9;
      font-family: 'Segoe UI', Arial, sans-serif;
    }
    .sidebar-panel {
      background: white;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .main-panel {
      background: white;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    h2 { color: #2c3e6b; font-weight: 700; }
    h4 { color: #555; }
    .anker-badge {
      display: inline-block;
      background: #2c3e6b;
      color: white;
      border-radius: 8px;
      padding: 6px 14px;
      margin: 4px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
    }
    .anker-badge.active {
      background: #e84545;
    }
    .info-box {
      background: #f0f4ff;
      border-left: 4px solid #2c3e6b;
      border-radius: 6px;
      padding: 12px 16px;
      margin-top: 10px;
      font-size: 13px;
    }
    #anker_buttons { margin: 12px 0; }
  "))),
  
  titlePanel(
    div(h2("📚 Veranstaltungs-Explorer"), style = "padding-bottom:0")
  ),
  
  sidebarLayout(
    sidebarPanel(
      width = 3,
      div(class = "sidebar-panel",
          h4("Veranstaltung wählen"),
          selectInput(
            "veranstaltung",
            label    = NULL,
            choices  = c("— bitte wählen —", sort(unique(df$Veranstaltungstitel))),
            selected = "— bitte wählen —",
            width    = "100%"
          ),
          hr(),
          h4("AnkerID"),
          uiOutput("anker_buttons"),
          hr(),
          uiOutput("detail_box")
      )
    ),
    
    mainPanel(
      width = 9,
      div(class = "main-panel",
          h4("Studiengänge & Abschlüsse", style = "margin-top:0"),
          uiOutput("no_selection_msg"),
          plotOutput("bubble_plot", height = "500px"),
          uiOutput("pruefung_table")
      )
    )
  )
)

# ── Server ────────────────────────────────────────────────────────────────────
server <- function(input, output, session) {
  
  # Filter to chosen Veranstaltung
  filtered_anker <- reactive({
    req(input$veranstaltung != "— bitte wählen —")
    df %>% filter(Veranstaltungstitel == input$veranstaltung)
  })
  
  # Unique AnkerIDs for this Veranstaltung
  anker_ids <- reactive({
    sort(unique(filtered_anker()$AnkerID))
  })
  
  # Selected AnkerID (stored in reactiveVal)
  selected_anker <- reactiveVal(NULL)
  
  # Reset when Veranstaltung changes
  observeEvent(input$veranstaltung, {
    selected_anker(NULL)
  })
  
  # Render AnkerID buttons
  output$anker_buttons <- renderUI({
    req(input$veranstaltung != "— bitte wählen —")
    ids <- anker_ids()
    if (length(ids) == 0) return(p("Keine AnkerIDs gefunden."))
    
    btn_list <- lapply(ids, function(id) {
      active_class <- if (!is.null(selected_anker()) && selected_anker() == id) "active" else ""
      tags$span(
        class = paste("anker-badge", active_class),
        onclick = sprintf("Shiny.setInputValue('anker_click', '%s', {priority: 'event'})", id),
        id
      )
    })
    div(id = "anker_buttons", btn_list)
  })
  
  # React to AnkerID button clicks
  observeEvent(input$anker_click, {
    selected_anker(input$anker_click)
  })
  
  # Data for selected AnkerID
  anker_data <- reactive({
    req(selected_anker())
    filtered_anker() %>% filter(AnkerID == selected_anker())
  })
  
  # Sidebar detail box
  output$detail_box <- renderUI({
    req(selected_anker())
    n <- nrow(anker_data())
    div(class = "info-box",
        tags$b("AnkerID: "), selected_anker(), tags$br(),
        tags$b("Einträge: "), n, tags$br(),
        tags$b("Studiengänge: "), n_distinct(anker_data()$Studiengang)
    )
  })
  
  # Hint when nothing selected
  output$no_selection_msg <- renderUI({
    if (input$veranstaltung == "— bitte wählen —") {
      div(
        style = "text-align:center; color:#aaa; margin-top:80px; font-size:16px;",
        "👆 Bitte eine Veranstaltung und dann eine AnkerID auswählen"
      )
    } else if (is.null(selected_anker())) {
      div(
        style = "text-align:center; color:#aaa; margin-top:80px; font-size:16px;",
        "👈 Bitte eine AnkerID auswählen"
      )
    }
  })
  
  # Bubble plot
  output$bubble_plot <- renderPlot({
    req(selected_anker(), nrow(anker_data()) > 0)
    
    plot_data <- anker_data() %>%
      group_by(Studiengang, Abschluss) %>%
      summarise(count = n(), .groups = "drop")
    
    ggplot(plot_data, aes(
      x     = Abschluss,
      y     = Studiengang,
      size  = count,
      fill  = Abschluss,
      label = Studiengang
    )) +
      geom_point(shape = 21, alpha = 0.85, color = "white", stroke = 1.5) +
      geom_text(aes(label = Studiengang), size = 3.5, fontface = "bold",
                vjust = -1.6, color = "#333") +
      geom_text(aes(label = paste0("n=", count)), size = 3, color = "#555",
                vjust = 3) +
      scale_size_continuous(range = c(10, 40), guide = "none") +
      scale_fill_manual(
        values = c(
          "Bachelor" = "#2c7bb6",
          "Master"   = "#e84545",
          "Diplom"   = "#f4a261",
          "PhD"      = "#6a4c93"
        ),
        na.value = "#999"
      ) +
      labs(
        title    = paste0("AnkerID: ", selected_anker()),
        subtitle = paste0("Veranstaltung: ", input$veranstaltung),
        x        = "Abschluss",
        y        = "Studiengang",
        fill     = "Abschluss"
      ) +
      theme_minimal(base_size = 13) +
      theme(
        plot.title      = element_text(face = "bold", color = "#2c3e6b", size = 16),
        plot.subtitle   = element_text(color = "#777", size = 12),
        panel.grid.major = element_line(color = "#eee"),
        panel.grid.minor = element_blank(),
        axis.text       = element_text(color = "#444"),
        legend.position = "top"
      )
  })
  
  # Prüfungstext table below the plot
  output$pruefung_table <- renderUI({
    req(selected_anker(), nrow(anker_data()) > 0)
    
    rows <- anker_data() %>%
      select(Studiengang, Abschluss, Prüfungstext) %>%
      distinct()
    
    table_rows <- apply(rows, 1, function(r) {
      tags$tr(
        tags$td(r["Studiengang"], style = "padding:6px 12px;"),
        tags$td(r["Abschluss"],   style = "padding:6px 12px;"),
        tags$td(r["Prüfungstext"], style = "padding:6px 12px; color:#555;")
      )
    })
    
    div(
      style = "margin-top:24px;",
      h4("Prüfungstexte", style = "color:#2c3e6b;"),
      tags$table(
        style = "width:100%; border-collapse:collapse; font-size:13px;",
        tags$thead(
          tags$tr(style = "background:#2c3e6b; color:white;",
                  tags$th("Studiengang",  style = "padding:8px 12px; text-align:left;"),
                  tags$th("Abschluss",    style = "padding:8px 12px; text-align:left;"),
                  tags$th("Prüfungstext", style = "padding:8px 12px; text-align:left;")
          )
        ),
        tags$tbody(table_rows)
      )
    )
  })
}

shinyApp(ui, server)