# Vision Mode

Process images, charts, diagrams, and visual content within documents using AI vision capabilities.

## Overview

Vision Mode enables WYN360 CLI to understand and analyze visual content in documents, providing insights from charts, diagrams, screenshots, and other images.

## Supported Formats

- **Word Documents** (.docx) - Images, charts, diagrams
- **PDF Files** (.pdf) - Scanned documents, technical diagrams
- **Excel Files** (.xlsx) - Embedded charts and visualizations
- **Direct Images** (.png, .jpg, .gif) - Screenshots, diagrams

## Processing Modes

### Skip Mode (Default)
```
You: Read report.docx

WYN360: [Processes text only, ignores images]
# Cost: $0.00 for images
```

### Describe Mode
```
You: Read report.docx with describe mode

WYN360: [Extracts alt text and captions only]
📊 [Image 1]: Revenue chart showing quarterly data
📐 [Image 2]: System architecture diagram
# Cost: $0.00 for images (no API calls)
```

### Vision Mode
```
You: Read report.docx with vision mode

WYN360: [Full AI analysis of images]
📊 **[Image 1]:** Bar chart showing quarterly revenue growth from Q1 to Q4.
Q4 shows the highest revenue at approximately $2.5M, representing a 23%
increase from Q3. All quarters show positive growth year-over-year.

📐 **[Image 2]:** System architecture diagram depicting three layers:
frontend (React), API layer (FastAPI), and database (PostgreSQL).
Shows data flow from user requests through authentication middleware.

💰 **Vision API Cost:** $0.06 (2 images processed)
```

## Use Cases

### Technical Documentation
- **Architecture Diagrams** - Understand system designs
- **Flowcharts** - Process workflow analysis
- **UML Diagrams** - Class and sequence diagram interpretation

### Data Analysis
- **Charts & Graphs** - Extract insights from visualizations
- **Dashboards** - Understand KPIs and metrics
- **Infographics** - Convert visual data to text insights

### UI/UX Design
- **Mockups** - Analyze interface designs
- **Wireframes** - Understand user flow
- **Screenshots** - Capture current state for analysis

## Cost Management

### Vision API Pricing
- **Cost per Image:** ~$0.01-0.05 depending on complexity
- **Separate Tracking** - Vision costs shown separately from text processing
- **Token Efficiency** - Smart chunking reduces processing costs

### Usage Examples
```
Document with 5 images:
- Text processing: 2,000 tokens = $0.006
- Vision processing: 5 images = $0.15
- Total cost: ~$0.156
```

## Configuration

```yaml
# Vision processing settings
vision_mode: "skip"        # skip, describe, vision
vision_batch_size: 5       # Process images in batches
vision_quality: "standard" # standard, high
```

## Examples

See [Usage Examples](../usage/use-cases.md#vision-mode-examples) for detailed workflows with visual content processing.