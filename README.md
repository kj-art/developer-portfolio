# Automation Engineering Portfolio

**Professional automation solutions for business process optimization and data pipeline management**

This repository showcases production-ready automation tools and libraries designed to eliminate manual workflows, reduce errors, and increase operational efficiency across diverse business environments.

## 🎯 Core Expertise

**Business Process Automation** • **Data Pipeline Engineering** • **API Integration** • **Workflow Orchestration**

- **18+ years** of pipeline automation experience in complex, deadline-driven production environments
- Proven track record of identifying workflow bottlenecks and building automated solutions that save hundreds of hours per project
- Expertise in cross-system integration, data processing, and scalable automation architecture

## 🚀 Featured Projects

### [StringSmith Template Formatter](./shared_utils/stringsmith/)
Professional Python library for conditional template formatting with rich styling and dynamic content control.

**Key Features:**
- Conditional sections that disappear when data is missing (eliminates manual null checking)
- Rich ANSI formatting with colors and text emphasis
- Multi-parameter custom functions for complex business logic
- Thread-safe, performance-optimized for high-frequency operations
- Comprehensive test suite with 95%+ coverage

**Business Value:** Perfect for application logging, CLI interfaces, business reporting, and any scenario requiring adaptive text output.

```python
# Templates automatically adapt based on available data
formatter = TemplateFormatter("{{User: ;name;}} {{?is_urgent;🚨 URGENT: ;}} {{message}}")
formatter.format(name="admin", message="Server maintenance")  # "User: admin Server maintenance"
formatter.format(message="System alert", urgent=True)         # "🚨 URGENT: System alert"
```

### [Multi-File Data Processing Pipeline](./data_pipeline/)
Enterprise-grade data processing system with streaming optimization and schema detection.

**Key Features:**
- **Streaming Processing:** Memory-efficient handling of large datasets
- **Schema Detection:** Automatic column normalization across file formats (CSV, Excel, JSON)
- **Index Management:** Configurable indexing strategies for different business needs
- **Error Recovery:** Robust handling of malformed files and edge cases
- **CLI & GUI Interfaces:** Professional user experience for technical and non-technical users

**Business Value:** Solves the universal problem of merging messy data from multiple sources into clean, standardized datasets. Critical for data migration, reporting consolidation, and ETL workflows.

### [Batch Rename Tool](./batch_rename/)
Flexible file renaming automation with modular processing pipeline and custom function support.

**Key Features:**
- **Modular Pipeline:** Extract, convert, template, and filter operations with custom functions
- **Preview Mode:** See changes before applying them
- **Collision Handling:** Configurable strategies for duplicate filenames
- **CLI & GUI:** Both command-line and graphical interfaces
- **Custom Functions:** Load and execute user-defined Python functions for specialized workflows

**Business Value:** Essential for digital asset management, batch processing workflows, and maintaining consistent file naming conventions across teams.

## 🛠️ Technical Stack

**Languages:** Python 3.7+  
**Data Processing:** pandas, openpyxl, streaming algorithms, schema detection  
**CLI/GUI:** argparse, PyQt6, professional user interface design  
**Testing & Quality:** pytest, comprehensive test coverage, error handling  
**Architecture:** Dependency injection, strategy pattern, modular design

## 🏗️ Architecture Philosophy

**Design Principles:**
- **CLI-first development** with GUI conversion capability
- **Streaming-optimized** for large dataset handling
- **Configuration-driven** behavior for business flexibility
- **Comprehensive error handling** for production reliability
- **Modular, testable architecture** for maintainability

**Professional Patterns:**
- Dependency injection for service composition
- Strategy pattern for processing algorithm selection
- Command pattern for CLI interface design
- Observer pattern for progress monitoring and logging

## 📊 Real-World Impact

**Production Environment Experience:**
- Automated data transfer between multiple software applications, eliminating manual file handling
- Built task-tracking automation enabling real-time progress monitoring across departments  
- Created import/export solutions handling complex file format conversions
- Developed automated quality assurance systems detecting production errors before final output

**Measurable Results:**
- Eliminated hundreds of hours of manual labor per project
- Dramatically improved consistency across production processes
- Reduced error rates through automated validation and quality checks
- Enabled scalable workflows supporting teams of 50+ contributors

## 🎨 Background & Unique Perspective

My experience in high-pressure animation production environments provides a unique perspective on automation challenges:

- **Complex multi-department workflows** requiring seamless tool integration
- **Tight deadline environments** where efficiency improvements have immediate impact
- **Cross-functional collaboration** between technical and creative teams
- **Quality-critical processes** where errors have significant downstream costs

This background translates directly to business automation: understanding how teams actually work, identifying bottlenecks that aren't obvious from specifications, and building tools that people will actually use.

## 📈 Professional Development

**Current Focus:** Building comprehensive automation toolkit demonstrating enterprise-ready solutions for common business challenges.

**Technical Growth:** Expanding expertise in modern frameworks, cloud platforms, and API integration while maintaining focus on practical, production-ready solutions.

**Learning Approach:** Production-quality implementations with real-world testing, comprehensive documentation, and professional deployment patterns.

## 🔗 Connect

**LinkedIn:** [Krishna Jain](https://www.linkedin.com/in/krishna-jain-938b7222)  
**Email:** krishna@krishnajain.com  

---

*Building automation solutions that eliminate repetitive work and empower teams to focus on high-value activities.*