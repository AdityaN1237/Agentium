"""
Comprehensive Database Seed Script for AI Job Recommendation System.
Populates MongoDB with realistic candidates, jobs, skills taxonomy, and documents.
"""
import asyncio
from datetime import datetime, timedelta
import random
from app.database import Database

# ============================================================================
# SKILL TAXONOMY - Hierarchical skill definitions with relationships
# ============================================================================
SKILL_TAXONOMY = [
    # Programming Languages
    {"name": "Python", "category": "Programming Languages", "related_skills": ["FastAPI", "Django", "Flask", "NumPy", "Pandas"], "child_skills": ["FastAPI", "Django", "Flask", "PyTorch", "TensorFlow"]},
    {"name": "JavaScript", "category": "Programming Languages", "related_skills": ["TypeScript", "Node.js", "React", "Vue.js", "Angular"], "child_skills": ["TypeScript", "Node.js", "React", "Vue.js"]},
    {"name": "TypeScript", "category": "Programming Languages", "related_skills": ["JavaScript", "Node.js", "React", "Angular", "NestJS"], "child_skills": []},
    {"name": "Java", "category": "Programming Languages", "related_skills": ["Spring Boot", "Hibernate", "Maven", "Gradle", "Kotlin"], "child_skills": ["Spring Boot", "Hibernate"]},
    {"name": "Go", "category": "Programming Languages", "related_skills": ["Kubernetes", "Docker", "gRPC", "Gin", "Fiber"], "child_skills": ["Gin", "Fiber"]},
    {"name": "Rust", "category": "Programming Languages", "related_skills": ["WebAssembly", "Tokio", "Actix", "Systems Programming"], "child_skills": []},
    {"name": "C++", "category": "Programming Languages", "related_skills": ["C", "Systems Programming", "Embedded", "Game Development"], "child_skills": []},
    {"name": "C#", "category": "Programming Languages", "related_skills": [".NET", "Unity", "ASP.NET", "Azure"], "child_skills": [".NET", "ASP.NET"]},
    {"name": "Ruby", "category": "Programming Languages", "related_skills": ["Ruby on Rails", "Sinatra", "RSpec"], "child_skills": ["Ruby on Rails"]},
    {"name": "PHP", "category": "Programming Languages", "related_skills": ["Laravel", "Symfony", "WordPress", "Composer"], "child_skills": ["Laravel", "Symfony"]},
    {"name": "Kotlin", "category": "Programming Languages", "related_skills": ["Android", "Java", "Spring Boot", "Ktor"], "child_skills": []},
    {"name": "Swift", "category": "Programming Languages", "related_skills": ["iOS", "UIKit", "SwiftUI", "Xcode"], "child_skills": ["SwiftUI"]},
    
    # Frontend Frameworks
    {"name": "React", "category": "Frontend", "related_skills": ["JavaScript", "TypeScript", "Redux", "Next.js", "React Native"], "child_skills": ["Redux", "Next.js", "React Native"]},
    {"name": "Vue.js", "category": "Frontend", "related_skills": ["JavaScript", "Vuex", "Nuxt.js", "TypeScript"], "child_skills": ["Vuex", "Nuxt.js"]},
    {"name": "Angular", "category": "Frontend", "related_skills": ["TypeScript", "RxJS", "NgRx", "HTML", "CSS"], "child_skills": ["NgRx"]},
    {"name": "Next.js", "category": "Frontend", "related_skills": ["React", "TypeScript", "Vercel", "SSR"], "child_skills": []},
    {"name": "Svelte", "category": "Frontend", "related_skills": ["JavaScript", "SvelteKit", "TypeScript"], "child_skills": ["SvelteKit"]},
    {"name": "HTML", "category": "Frontend", "related_skills": ["CSS", "JavaScript", "Accessibility", "SEO"], "child_skills": []},
    {"name": "CSS", "category": "Frontend", "related_skills": ["HTML", "Sass", "Tailwind CSS", "Bootstrap"], "child_skills": ["Sass", "Tailwind CSS"]},
    {"name": "Tailwind CSS", "category": "Frontend", "related_skills": ["CSS", "React", "Vue.js", "Next.js"], "child_skills": []},
    
    # Backend Frameworks
    {"name": "FastAPI", "category": "Backend", "related_skills": ["Python", "Pydantic", "SQLAlchemy", "Async"], "child_skills": []},
    {"name": "Django", "category": "Backend", "related_skills": ["Python", "Django REST Framework", "PostgreSQL", "Celery"], "child_skills": ["Django REST Framework"]},
    {"name": "Flask", "category": "Backend", "related_skills": ["Python", "SQLAlchemy", "Jinja2", "REST API"], "child_skills": []},
    {"name": "Node.js", "category": "Backend", "related_skills": ["JavaScript", "Express.js", "NestJS", "TypeScript"], "child_skills": ["Express.js", "NestJS"]},
    {"name": "Express.js", "category": "Backend", "related_skills": ["Node.js", "JavaScript", "MongoDB", "REST API"], "child_skills": []},
    {"name": "Spring Boot", "category": "Backend", "related_skills": ["Java", "Hibernate", "Maven", "Microservices"], "child_skills": []},
    {"name": "NestJS", "category": "Backend", "related_skills": ["Node.js", "TypeScript", "GraphQL", "Microservices"], "child_skills": []},
    {"name": "Ruby on Rails", "category": "Backend", "related_skills": ["Ruby", "PostgreSQL", "ActiveRecord", "REST API"], "child_skills": []},
    {"name": "Laravel", "category": "Backend", "related_skills": ["PHP", "MySQL", "Eloquent", "Blade"], "child_skills": []},
    {"name": ".NET", "category": "Backend", "related_skills": ["C#", "ASP.NET", "Azure", "Entity Framework"], "child_skills": ["ASP.NET"]},
    
    # Databases
    {"name": "PostgreSQL", "category": "Databases", "related_skills": ["SQL", "Database Design", "Django", "SQLAlchemy"], "child_skills": []},
    {"name": "MongoDB", "category": "Databases", "related_skills": ["NoSQL", "Node.js", "Mongoose", "Atlas"], "child_skills": []},
    {"name": "MySQL", "category": "Databases", "related_skills": ["SQL", "Database Design", "Laravel", "PHP"], "child_skills": []},
    {"name": "Redis", "category": "Databases", "related_skills": ["Caching", "Session Management", "Pub/Sub"], "child_skills": []},
    {"name": "Elasticsearch", "category": "Databases", "related_skills": ["Search", "Logging", "Kibana", "Full-text Search"], "child_skills": []},
    {"name": "DynamoDB", "category": "Databases", "related_skills": ["AWS", "NoSQL", "Serverless"], "child_skills": []},
    {"name": "SQL", "category": "Databases", "related_skills": ["PostgreSQL", "MySQL", "Data Analysis", "Database Design"], "child_skills": []},
    
    # Cloud & DevOps
    {"name": "AWS", "category": "Cloud", "related_skills": ["EC2", "S3", "Lambda", "RDS", "CloudFormation"], "child_skills": ["EC2", "S3", "Lambda", "ECS"]},
    {"name": "Docker", "category": "DevOps", "related_skills": ["Kubernetes", "Containerization", "Docker Compose", "CI/CD"], "child_skills": ["Docker Compose"]},
    {"name": "Kubernetes", "category": "DevOps", "related_skills": ["Docker", "Helm", "AWS EKS", "GKE", "Container Orchestration"], "child_skills": ["Helm"]},
    {"name": "CI/CD", "category": "DevOps", "related_skills": ["Jenkins", "GitHub Actions", "GitLab CI", "CircleCI"], "child_skills": []},
    {"name": "Terraform", "category": "DevOps", "related_skills": ["Infrastructure as Code", "AWS", "Azure", "GCP"], "child_skills": []},
    {"name": "GitHub Actions", "category": "DevOps", "related_skills": ["CI/CD", "GitHub", "Automation", "DevOps"], "child_skills": []},
    {"name": "Azure", "category": "Cloud", "related_skills": ["Azure DevOps", "Azure Functions", ".NET", "C#"], "child_skills": []},
    {"name": "GCP", "category": "Cloud", "related_skills": ["BigQuery", "Cloud Run", "Kubernetes", "Firebase"], "child_skills": ["Firebase"]},
    {"name": "Linux", "category": "DevOps", "related_skills": ["Bash", "Shell Scripting", "System Administration"], "child_skills": []},
    
    # AI/ML
    {"name": "Machine Learning", "category": "AI/ML", "related_skills": ["Python", "TensorFlow", "PyTorch", "Scikit-learn"], "child_skills": ["Deep Learning", "NLP"]},
    {"name": "Deep Learning", "category": "AI/ML", "related_skills": ["TensorFlow", "PyTorch", "Neural Networks", "Computer Vision"], "child_skills": []},
    {"name": "TensorFlow", "category": "AI/ML", "related_skills": ["Python", "Keras", "Deep Learning", "Machine Learning"], "child_skills": ["Keras"]},
    {"name": "PyTorch", "category": "AI/ML", "related_skills": ["Python", "Deep Learning", "Computer Vision", "NLP"], "child_skills": []},
    {"name": "NLP", "category": "AI/ML", "related_skills": ["Python", "Transformers", "BERT", "GPT", "LangChain"], "child_skills": ["LangChain"]},
    {"name": "Computer Vision", "category": "AI/ML", "related_skills": ["OpenCV", "TensorFlow", "PyTorch", "Image Processing"], "child_skills": []},
    {"name": "LLM", "category": "AI/ML", "related_skills": ["OpenAI", "LangChain", "Prompt Engineering", "RAG"], "child_skills": []},
    {"name": "Data Science", "category": "AI/ML", "related_skills": ["Python", "Pandas", "NumPy", "Matplotlib", "Jupyter"], "child_skills": []},
    
    # Other
    {"name": "GraphQL", "category": "API", "related_skills": ["Apollo", "REST API", "Node.js", "TypeScript"], "child_skills": []},
    {"name": "REST API", "category": "API", "related_skills": ["HTTP", "JSON", "FastAPI", "Express.js"], "child_skills": []},
    {"name": "Git", "category": "Tools", "related_skills": ["GitHub", "GitLab", "Version Control", "Branching"], "child_skills": []},
    {"name": "Agile", "category": "Methodology", "related_skills": ["Scrum", "Kanban", "Jira", "Sprint Planning"], "child_skills": ["Scrum"]},
    {"name": "Microservices", "category": "Architecture", "related_skills": ["Docker", "Kubernetes", "API Gateway", "Event-Driven"], "child_skills": []},
]

# ============================================================================
# CANDIDATES - Realistic candidate profiles
# ============================================================================
CANDIDATES = [
    {
        "name": "Rahul Sharma",
        "email": "rahul.sharma@email.com",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "resume_text": """Senior Backend Engineer with 6+ years of experience building scalable microservices.
        Expert in Python ecosystem including FastAPI, Django, and async programming.
        Led development of high-throughput payment processing system handling 10M+ transactions daily.
        Strong experience with AWS (EC2, Lambda, S3, RDS) and containerization with Docker/Kubernetes.
        Passionate about clean code, test-driven development, and mentoring junior developers.""",
        "experience_years": 6,
        "preferences": ["Backend", "Python", "Remote"]
    },
    {
        "name": "Priya Patel",
        "email": "priya.patel@email.com",
        "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "Node.js"],
        "resume_text": """Frontend Developer with 4 years of experience building modern web applications.
        Proficient in React, TypeScript, and Next.js for server-side rendering.
        Built responsive e-commerce platform serving 500K+ monthly active users.
        Strong focus on UI/UX, accessibility standards, and performance optimization.
        Experience with state management (Redux, Zustand) and API integration.""",
        "experience_years": 4,
        "preferences": ["Frontend", "React", "Startup"]
    },
    {
        "name": "Amit Kumar",
        "email": "amit.kumar@email.com",
        "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "NLP"],
        "resume_text": """Machine Learning Engineer with 5 years of experience in deep learning and NLP.
        Built production ML pipelines processing millions of documents daily.
        Expertise in transformer models, fine-tuning LLMs, and RAG systems.
        Published research in top-tier conferences (NeurIPS, ACL).
        Strong background in MLOps with Kubeflow, MLflow, and model deployment.""",
        "experience_years": 5,
        "preferences": ["AI/ML", "NLP", "Research"]
    },
    {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "skills": ["Java", "Spring Boot", "Kubernetes", "AWS", "Microservices"],
        "resume_text": """Principal Software Engineer with 10+ years of experience in enterprise systems.
        Architected microservices platform serving Fortune 500 clients.
        Expert in Java ecosystem including Spring Boot, Hibernate, and Kafka.
        Led migration of monolithic application to Kubernetes, reducing costs by 40%.
        Certified AWS Solutions Architect and Kubernetes Administrator.""",
        "experience_years": 10,
        "preferences": ["Backend", "Architecture", "Leadership"]
    },
    {
        "name": "Michael Chen",
        "email": "michael.chen@email.com",
        "skills": ["Go", "Kubernetes", "Docker", "Terraform", "CI/CD"],
        "resume_text": """DevOps Engineer with 7 years of experience in cloud infrastructure.
        Built and maintained Kubernetes clusters processing 1B+ daily requests.
        Expert in Infrastructure as Code with Terraform and Pulumi.
        Implemented GitOps workflows reducing deployment time by 80%.
        Strong experience with monitoring (Prometheus, Grafana) and logging (ELK stack).""",
        "experience_years": 7,
        "preferences": ["DevOps", "Cloud", "Infrastructure"]
    },
    {
        "name": "Aisha Rahman",
        "email": "aisha.rahman@email.com",
        "skills": ["React", "React Native", "TypeScript", "GraphQL", "Node.js"],
        "resume_text": """Full Stack Developer specializing in React and React Native with 5 years experience.
        Built cross-platform mobile apps with shared codebase serving 1M+ users.
        Strong expertise in GraphQL APIs and real-time applications.
        Experience with app store deployment, push notifications, and analytics.
        Passionate about mobile UX and performance optimization.""",
        "experience_years": 5,
        "preferences": ["Mobile", "React Native", "Full Stack"]
    },
    {
        "name": "David Wilson",
        "email": "david.wilson@email.com",
        "skills": ["Python", "Django", "PostgreSQL", "Redis", "Celery"],
        "resume_text": """Backend Developer with 4 years of experience in Django ecosystem.
        Built RESTful APIs powering SaaS platforms with 100K+ users.
        Expert in database optimization, caching strategies, and async task queues.
        Experience with payment integrations (Stripe, PayPal) and third-party APIs.
        Strong testing practices with pytest and integration testing.""",
        "experience_years": 4,
        "preferences": ["Backend", "Django", "SaaS"]
    },
    {
        "name": "Emily Zhang",
        "email": "emily.zhang@email.com",
        "skills": ["JavaScript", "Vue.js", "Nuxt.js", "CSS", "Node.js"],
        "resume_text": """Frontend Developer with 3 years of experience in Vue.js ecosystem.
        Built interactive dashboards and data visualization applications.
        Proficient in Nuxt.js for SSR and static site generation.
        Strong CSS skills including animations and responsive design.
        Experience with design systems and component libraries.""",
        "experience_years": 3,
        "preferences": ["Frontend", "Vue.js", "Design"]
    },
    {
        "name": "James Miller",
        "email": "james.miller@email.com",
        "skills": ["Rust", "Go", "Docker", "Linux", "Systems Programming"],
        "resume_text": """Systems Engineer with 8 years of experience in low-level programming.
        Built high-performance network proxies handling 100K concurrent connections.
        Expert in Rust for memory-safe systems programming.
        Strong Linux kernel knowledge and performance tuning experience.
        Contributed to open-source projects in infrastructure space.""",
        "experience_years": 8,
        "preferences": ["Systems", "Infrastructure", "Open Source"]
    },
    {
        "name": "Neha Gupta",
        "email": "neha.gupta@email.com",
        "skills": ["Python", "Data Science", "SQL", "Machine Learning", "Pandas"],
        "resume_text": """Data Scientist with 4 years of experience in analytics and ML.
        Built ML models improving customer retention by 25%.
        Expert in Python data stack (Pandas, NumPy, Scikit-learn).
        Strong SQL skills for complex data analysis and ETL pipelines.
        Experience with A/B testing and statistical analysis.""",
        "experience_years": 4,
        "preferences": ["Data Science", "Analytics", "Product"]
    },
    {
        "name": "Alex Thompson",
        "email": "alex.thompson@email.com",
        "skills": ["Swift", "iOS", "SwiftUI", "Xcode", "Core Data"],
        "resume_text": """iOS Developer with 6 years of experience building native applications.
        Published 10+ apps on App Store with combined 5M+ downloads.
        Expert in SwiftUI and UIKit for modern iOS development.
        Strong experience with Core Data, CloudKit, and push notifications.
        Passionate about accessibility and Apple Human Interface Guidelines.""",
        "experience_years": 6,
        "preferences": ["iOS", "Mobile", "Apple"]
    },
    {
        "name": "Sophia Lee",
        "email": "sophia.lee@email.com",
        "skills": ["Kotlin", "Android", "Java", "Firebase", "Jetpack Compose"],
        "resume_text": """Android Developer with 5 years of experience in native mobile development.
        Built enterprise Android applications used by 500K+ employees globally.
        Expert in Kotlin and Jetpack Compose for modern Android UI.
        Strong experience with Firebase, Room, and Android Architecture Components.
        Experience with Google Play deployment and app optimization.""",
        "experience_years": 5,
        "preferences": ["Android", "Mobile", "Kotlin"]
    },
    {
        "name": "Robert Garcia",
        "email": "robert.garcia@email.com",
        "skills": ["AWS", "Terraform", "Python", "Kubernetes", "CI/CD"],
        "resume_text": """Cloud Architect with 9 years of experience designing scalable systems.
        Designed cloud infrastructure saving $2M annually in operating costs.
        Multiple AWS certifications (Solutions Architect Pro, DevOps Engineer).
        Expert in Infrastructure as Code with Terraform and CloudFormation.
        Led cloud migration projects for Fortune 500 companies.""",
        "experience_years": 9,
        "preferences": ["Cloud", "Architecture", "AWS"]
    },
    {
        "name": "Lisa Wang",
        "email": "lisa.wang@email.com",
        "skills": ["C#", ".NET", "Azure", "SQL", "Microservices"],
        "resume_text": """Senior .NET Developer with 7 years of experience in enterprise software.
        Built high-volume transaction processing systems for financial sector.
        Expert in .NET Core, Entity Framework, and Azure services.
        Strong experience with Azure DevOps and CI/CD pipelines.
        Microsoft Certified Azure Developer Associate.""",
        "experience_years": 7,
        "preferences": ["Backend", ".NET", "Enterprise"]
    },
    {
        "name": "Kevin Brown",
        "email": "kevin.brown@email.com",
        "skills": ["Node.js", "Express.js", "MongoDB", "Redis", "Docker"],
        "resume_text": """Backend Developer with 4 years of experience in Node.js ecosystem.
        Built real-time chat systems handling 50K concurrent users.
        Expert in Express.js, MongoDB, and Redis for caching.
        Experience with WebSocket implementations and event-driven architecture.
        Strong focus on API design and documentation.""",
        "experience_years": 4,
        "preferences": ["Backend", "Node.js", "Real-time"]
    },
    {
        "name": "Jennifer Davis",
        "email": "jennifer.davis@email.com",
        "skills": ["React", "Angular", "TypeScript", "CSS", "Git"],
        "resume_text": """Frontend Developer with 5 years of experience in both React and Angular.
        Led frontend team of 6 developers building customer-facing applications.
        Expert in TypeScript, CSS-in-JS, and modern build tools.
        Strong focus on testing (Jest, Cypress) and code quality.
        Experience with micro-frontend architecture.""",
        "experience_years": 5,
        "preferences": ["Frontend", "Leadership", "Enterprise"]
    },
    {
        "name": "Daniel Martinez",
        "email": "daniel.martinez@email.com",
        "skills": ["PHP", "Laravel", "MySQL", "Vue.js", "Redis"],
        "resume_text": """Full Stack Developer with 6 years of experience in LAMP stack.
        Built e-commerce platforms processing $50M+ annual transactions.
        Expert in Laravel, MySQL optimization, and queue management.
        Experience with payment gateways and inventory management systems.
        Strong understanding of security best practices.""",
        "experience_years": 6,
        "preferences": ["Full Stack", "E-commerce", "PHP"]
    },
    {
        "name": "Ananya Reddy",
        "email": "ananya.reddy@email.com",
        "skills": ["Python", "LLM", "LangChain", "NLP", "FastAPI"],
        "resume_text": """AI Engineer specializing in LLM applications with 3 years of experience.
        Built RAG systems and AI chatbots for enterprise customers.
        Expert in LangChain, OpenAI APIs, and prompt engineering.
        Experience with vector databases (Pinecone, Weaviate) and embeddings.
        Strong background in backend development with FastAPI.""",
        "experience_years": 3,
        "preferences": ["AI/ML", "LLM", "Startup"]
    },
    {
        "name": "Chris Anderson",
        "email": "chris.anderson@email.com",
        "skills": ["Ruby", "Ruby on Rails", "PostgreSQL", "Redis", "Heroku"],
        "resume_text": """Ruby on Rails Developer with 8 years of experience building web applications.
        Built SaaS products from scratch to 100K+ paying customers.
        Expert in Rails, ActiveRecord, and Sidekiq for background jobs.
        Strong experience with Heroku, AWS, and database scaling.
        Open source contributor to Ruby gems ecosystem.""",
        "experience_years": 8,
        "preferences": ["Backend", "Ruby", "Startup"]
    },
    {
        "name": "Meera Krishnan",
        "email": "meera.krishnan@email.com",
        "skills": ["Python", "Django", "React", "PostgreSQL", "Docker"],
        "resume_text": """Full Stack Developer with 5 years of experience in Django and React.
        Built healthcare platforms handling sensitive patient data (HIPAA compliant).
        Expert in Django REST Framework and React integration.
        Strong focus on security, testing, and documentation.
        Experience with Docker, CI/CD, and AWS deployment.""",
        "experience_years": 5,
        "preferences": ["Full Stack", "Healthcare", "Python"]
    },
]

# ============================================================================
# JOBS - Realistic job postings
# ============================================================================
JOBS = [
    {
        "title": "Senior Backend Engineer",
        "company": "TechCorp Solutions",
        "description": """We're looking for a Senior Backend Engineer to join our growing team.
        You'll be working on our core payment processing platform that handles millions of transactions.
        
        Requirements:
        - 5+ years of experience with Python and FastAPI or Django
        - Strong experience with PostgreSQL and database optimization
        - Experience with Docker, Kubernetes, and AWS
        - Understanding of microservices architecture
        - Excellent problem-solving and communication skills
        
        Nice to have:
        - Experience with async programming
        - Familiarity with event-driven systems (Kafka, RabbitMQ)
        - Open source contributions""",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "location": "Remote",
        "salary_range": "$150,000 - $200,000"
    },
    {
        "title": "Frontend Developer - React",
        "company": "InnovateTech Inc",
        "description": """Join our frontend team to build beautiful, performant web applications.
        You'll work closely with designers and backend engineers to deliver exceptional user experiences.
        
        Requirements:
        - 3+ years of experience with React and TypeScript
        - Strong understanding of modern CSS and responsive design
        - Experience with state management (Redux, Zustand, or similar)
        - Knowledge of testing frameworks (Jest, React Testing Library)
        
        Nice to have:
        - Experience with Next.js
        - Familiarity with GraphQL
        - Understanding of accessibility standards""",
        "required_skills": ["React", "TypeScript", "CSS", "Redux"],
        "location": "San Francisco, CA",
        "salary_range": "$120,000 - $160,000"
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Dynamics",
        "description": """We're building the future of AI-powered enterprise software.
        As an ML Engineer, you'll develop and deploy production machine learning models.
        
        Requirements:
        - 4+ years of experience in machine learning
        - Proficiency in Python, TensorFlow or PyTorch
        - Experience with NLP and transformer models
        - Strong understanding of MLOps and model deployment
        - Excellent communication skills for cross-functional collaboration
        
        Nice to have:
        - Experience with LLMs and RAG systems
        - Published research or patents
        - Experience with distributed training""",
        "required_skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "NLP"],
        "location": "New York, NY",
        "salary_range": "$180,000 - $250,000"
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudScale Systems",
        "description": """Help us build and maintain our cloud infrastructure at scale.
        You'll be responsible for CI/CD pipelines, Kubernetes clusters, and monitoring systems.
        
        Requirements:
        - 5+ years of DevOps or SRE experience
        - Expert-level Kubernetes and Docker knowledge
        - Experience with Terraform or similar IaC tools
        - Strong scripting skills (Python, Bash, Go)
        - AWS, GCP, or Azure certification preferred
        
        Nice to have:
        - Experience with GitOps (ArgoCD, Flux)
        - Service mesh experience (Istio, Linkerd)
        - Security and compliance knowledge""",
        "required_skills": ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD"],
        "location": "Seattle, WA",
        "salary_range": "$160,000 - $210,000"
    },
    {
        "title": "Full Stack Developer",
        "company": "StartupHub",
        "description": """Join our fast-paced startup to build our next-generation SaaS platform.
        You'll wear many hats and have significant impact on our product direction.
        
        Requirements:
        - 3+ years of full stack development experience
        - Proficiency in React or Vue.js for frontend
        - Experience with Node.js or Python for backend
        - Database experience (PostgreSQL, MongoDB)
        - Comfortable with rapid iteration and agile methodologies
        
        Nice to have:
        - Experience with real-time features (WebSocket)
        - Understanding of payment integrations
        - Design sensibility""",
        "required_skills": ["React", "Node.js", "TypeScript", "PostgreSQL", "MongoDB"],
        "location": "Austin, TX",
        "salary_range": "$100,000 - $150,000"
    },
    {
        "title": "iOS Developer",
        "company": "MobileFirst Inc",
        "description": """Build native iOS applications that millions of users love.
        We're looking for someone passionate about mobile UX and Apple ecosystem.
        
        Requirements:
        - 4+ years of iOS development experience
        - Expert in Swift and SwiftUI
        - Experience with Core Data and CloudKit
        - Understanding of App Store guidelines and deployment
        - Strong attention to detail and design
        
        Nice to have:
        - Experience with ARKit or Core ML
        - Published apps with high ratings
        - Knowledge of Android development""",
        "required_skills": ["Swift", "iOS", "SwiftUI", "Xcode", "Core Data"],
        "location": "Los Angeles, CA",
        "salary_range": "$140,000 - $180,000"
    },
    {
        "title": "Java Backend Developer",
        "company": "Enterprise Solutions Ltd",
        "description": """Join our enterprise engineering team to build scalable microservices.
        You'll work on systems processing billions of events daily.
        
        Requirements:
        - 6+ years of Java development experience
        - Expert in Spring Boot and Hibernate
        - Experience with Kafka and event-driven architecture
        - Strong understanding of distributed systems
        - Experience with databases (PostgreSQL, Cassandra)
        
        Nice to have:
        - Kubernetes experience
        - AWS or Azure certification
        - Experience with legacy system modernization""",
        "required_skills": ["Java", "Spring Boot", "Hibernate", "Kafka", "Microservices"],
        "location": "Chicago, IL",
        "salary_range": "$150,000 - $200,000"
    },
    {
        "title": "Data Scientist",
        "company": "DataDriven Analytics",
        "description": """Apply machine learning to solve real business problems.
        Work with large datasets to derive insights and build predictive models.
        
        Requirements:
        - 3+ years of data science experience
        - Strong Python skills (Pandas, NumPy, Scikit-learn)
        - Experience with SQL and data warehousing
        - Statistical modeling and A/B testing experience
        - Excellent visualization and communication skills
        
        Nice to have:
        - Deep learning experience
        - Experience with Spark or Databricks
        - Domain expertise in e-commerce or fintech""",
        "required_skills": ["Python", "Data Science", "SQL", "Machine Learning", "Pandas"],
        "location": "Boston, MA",
        "salary_range": "$130,000 - $170,000"
    },
    {
        "title": ".NET Developer",
        "company": "FinTech Corp",
        "description": """Build high-performance trading systems for financial markets.
        Work with cutting-edge technology in a fast-paced environment.
        
        Requirements:
        - 5+ years of C# and .NET experience
        - Experience with Azure cloud services
        - Strong SQL Server knowledge
        - Understanding of financial systems
        - Excellent debugging and performance optimization skills
        
        Nice to have:
        - Experience with real-time systems
        - FIX protocol knowledge
        - Microservices architecture experience""",
        "required_skills": ["C#", ".NET", "Azure", "SQL", "Microservices"],
        "location": "New York, NY",
        "salary_range": "$160,000 - $220,000"
    },
    {
        "title": "Vue.js Frontend Developer",
        "company": "Creative Digital",
        "description": """Create beautiful interactive web experiences for our clients.
        You'll work with designers to bring stunning designs to life.
        
        Requirements:
        - 3+ years of frontend development experience
        - Expert in Vue.js and Nuxt.js
        - Strong CSS/SCSS skills
        - Experience with RESTful APIs and GraphQL
        - Eye for design and attention to detail
        
        Nice to have:
        - Animation experience (GSAP, Lottie)
        - 3D graphics (Three.js)
        - Accessibility expertise""",
        "required_skills": ["Vue.js", "Nuxt.js", "JavaScript", "CSS", "GraphQL"],
        "location": "Remote",
        "salary_range": "$100,000 - $140,000"
    },
    {
        "title": "Cloud Solutions Architect",
        "company": "GlobalTech Consulting",
        "description": """Design and implement cloud solutions for enterprise clients.
        Lead technical discussions and drive cloud transformation initiatives.
        
        Requirements:
        - 8+ years of IT experience with 5+ in cloud
        - AWS Solutions Architect Professional certification
        - Experience with Terraform and CloudFormation
        - Strong understanding of networking and security
        - Excellent presentation and client-facing skills
        
        Nice to have:
        - Multi-cloud experience (AWS, Azure, GCP)
        - Kubernetes expertise
        - Experience with compliance (HIPAA, SOC2)""",
        "required_skills": ["AWS", "Terraform", "Kubernetes", "Cloud Architecture", "DevOps"],
        "location": "Washington, DC",
        "salary_range": "$180,000 - $250,000"
    },
    {
        "title": "Ruby on Rails Developer",
        "company": "SaaSify Inc",
        "description": """Build and scale our core SaaS platform used by thousands of businesses.
        Work on performance optimization and new feature development.
        
        Requirements:
        - 5+ years of Ruby on Rails experience
        - Strong PostgreSQL and Redis experience
        - Experience with Sidekiq and background job processing
        - Understanding of testing (RSpec, Minitest)
        - API design experience
        
        Nice to have:
        - Hotwire/Stimulus experience
        - Frontend skills (React or Vue)
        - Experience with payment systems""",
        "required_skills": ["Ruby", "Ruby on Rails", "PostgreSQL", "Redis", "REST API"],
        "location": "Denver, CO",
        "salary_range": "$130,000 - $170,000"
    },
    {
        "title": "Android Developer",
        "company": "AppFactory Mobile",
        "description": """Build native Android applications for our diverse client base.
        Work with latest Android technologies and architecture patterns.
        
        Requirements:
        - 4+ years of Android development
        - Expert in Kotlin and Jetpack Compose
        - Experience with MVVM and Clean Architecture
        - Firebase and Google Play Services experience
        - Strong testing practices
        
        Nice to have:
        - iOS/Flutter cross-platform experience
        - CI/CD for mobile apps
        - Published apps on Play Store""",
        "required_skills": ["Kotlin", "Android", "Jetpack Compose", "Firebase", "MVVM"],
        "location": "Miami, FL",
        "salary_range": "$120,000 - $160,000"
    },
    {
        "title": "AI/LLM Engineer",
        "company": "NextGen AI Labs",
        "description": """Build production LLM applications and AI-powered features.
        Work on cutting-edge generative AI technology.
        
        Requirements:
        - 2+ years of experience with LLMs and AI applications
        - Strong Python and FastAPI skills
        - Experience with LangChain or similar frameworks
        - Understanding of RAG, embeddings, and vector databases
        - Prompt engineering expertise
        
        Nice to have:
        - Fine-tuning experience
        - Experience with multiple LLM providers
        - Research background in NLP""",
        "required_skills": ["Python", "LLM", "LangChain", "NLP", "FastAPI"],
        "location": "San Francisco, CA",
        "salary_range": "$180,000 - $280,000"
    },
    {
        "title": "Go Backend Developer",
        "company": "Infrastructure Labs",
        "description": """Build high-performance infrastructure tools and services.
        Work on distributed systems handling massive scale.
        
        Requirements:
        - 4+ years of Go development experience
        - Experience with distributed systems
        - Strong knowledge of networking and protocols
        - Kubernetes and container orchestration experience
        - Performance optimization expertise
        
        Nice to have:
        - Rust or C++ experience
        - Open source contributions
        - Experience with observability tools""",
        "required_skills": ["Go", "Kubernetes", "Docker", "Distributed Systems", "gRPC"],
        "location": "Remote",
        "salary_range": "$150,000 - $200,000"
    },
]

# ============================================================================
# DOCUMENTS - For RAG Q&A
# ============================================================================
DOCUMENTS = [
    {
        "title": "Employee Handbook - Leave Policy",
        "text": """Annual Leave Policy

All full-time employees are entitled to the following leave benefits:

1. Paid Time Off (PTO): 25 days per year, accruing monthly
2. Sick Leave: 10 days per year, no carryover
3. Parental Leave: 16 weeks paid leave for primary caregivers
4. Bereavement Leave: Up to 5 days for immediate family

Requesting Leave:
- Submit requests through the HR portal at least 2 weeks in advance
- Manager approval required for leaves exceeding 5 consecutive days
- Holiday blackout periods may apply during critical business periods

Carryover Policy:
- Up to 5 days of unused PTO can be carried to the next year
- Unused days beyond the limit will be forfeited on December 31st

For questions, contact HR at hr@company.com""",
        "source": "HR Portal",
        "tags": ["HR", "Leave", "Policy"]
    },
    {
        "title": "Remote Work Guidelines",
        "text": """Remote Work Policy

We embrace flexible work arrangements to support work-life balance.

Eligibility:
- All employees after completing 90-day probation period
- Approval from direct manager required
- Some roles may require minimum in-office days

Equipment:
- Company provides laptop, monitor, and essential peripherals
- Monthly stipend of $100 for internet and utilities
- Ergonomic equipment budget of $500 (one-time)

Communication Expectations:
- Available during core hours (10 AM - 4 PM local time)
- Respond to Slack messages within 4 hours
- Camera on for team meetings
- Weekly 1:1 with manager

Security Requirements:
- Use company VPN for all work activities
- Do not work from public networks without VPN
- Lock computer when stepping away
- Report any security incidents immediately

Contact IT support at support@company.com for technical issues.""",
        "source": "IT & HR",
        "tags": ["Remote Work", "Policy", "Equipment"]
    },
    {
        "title": "Engineering Standards and Best Practices",
        "text": """Engineering Best Practices

Code Quality:
- All code must pass automated linting and formatting checks
- Minimum 80% test coverage for new features
- Code review required from at least one team member
- Follow language-specific style guides (PEP8, ESLint, etc.)

Git Workflow:
- Use feature branches for all changes
- Branch naming: feature/, bugfix/, hotfix/ prefixes
- Squash commits before merging to main
- Write descriptive commit messages following conventional commits

Pull Request Guidelines:
- Include ticket number in PR title
- Add description of changes and testing performed
- Update documentation if applicable
- Address all review comments before merging

Deployment:
- All changes go through staging before production
- Use feature flags for risky changes
- Monitor error rates and performance after deployment
- On-call engineer must be available during deployments

Documentation:
- Keep README files up to date
- Document API endpoints in OpenAPI/Swagger
- Architecture decisions in ADR format""",
        "source": "Engineering",
        "tags": ["Engineering", "Code Review", "Best Practices"]
    },
    {
        "title": "Security Policy and Guidelines",
        "text": """Information Security Policy

Password Requirements:
- Minimum 12 characters
- Must include uppercase, lowercase, numbers, and symbols
- Change every 90 days
- No password reuse for last 10 passwords
- Use password manager (1Password provided)

Two-Factor Authentication:
- Required for all company accounts
- Use hardware keys (YubiKey) for administrative access
- Report lost devices immediately

Data Classification:
- Public: Marketing materials, public documentation
- Internal: Business documents, general communications
- Confidential: Customer data, financial information
- Restricted: Security credentials, encryption keys

Handling Sensitive Data:
- Never share credentials via email or Slack
- Use encrypted file sharing for sensitive documents
- Customer data must not leave approved systems
- Delete data according to retention policies

Incident Response:
- Report security incidents to security@company.com
- Do not attempt to investigate on your own
- Preserve evidence and document timeline
- Follow instructions from security team

Training:
- Complete annual security awareness training
- Phishing simulation exercises monthly
- Role-specific training for developers""",
        "source": "Security Team",
        "tags": ["Security", "Policy", "Compliance"]
    },
    {
        "title": "Performance Review Process",
        "text": """Performance Review Guidelines

Review Cycle:
- Annual comprehensive reviews in Q4
- Mid-year check-ins in Q2
- Continuous feedback throughout the year

Evaluation Criteria:
1. Goal Achievement (40%): Did you meet your OKRs?
2. Technical Skills (25%): Proficiency and growth
3. Collaboration (20%): Teamwork and communication
4. Company Values (15%): Alignment with culture

Self-Assessment:
- Complete self-review in Lattice by deadline
- Provide specific examples for each category
- Rate yourself honestly and constructively

Manager Review:
- Managers review self-assessments and peer feedback
- Schedule 1-hour review meeting
- Discuss strengths, areas for improvement, and goals

Rating Scale:
- Exceeds Expectations: Top 15% performance
- Meets Expectations: Solid contributor
- Developing: Growth areas identified
- Below Expectations: Performance improvement plan

Compensation:
- Merit increases based on performance rating
- Promotion eligibility after Exceeds rating
- Equity refresh for top performers

Career Development:
- Create development plan with manager
- Budget for training and conferences
- Internal mobility opportunities""",
        "source": "HR",
        "tags": ["Performance", "HR", "Career"]
    },
    {
        "title": "Expense Reimbursement Policy",
        "text": """Expense Policy

Travel Expenses:
- Book flights through Navan (formerly TripActions)
- Maximum hotel rate: $200/night (major cities may vary)
- Per diem for meals: $75/day domestic, $100/day international
- Economy class for flights under 6 hours

Reimbursable Expenses:
- Business meals with clients (require itemized receipt)
- Professional development courses (pre-approval required)
- Home office equipment (see Remote Work policy)
- Professional certifications and memberships

Non-Reimbursable:
- Personal travel extensions
- Alcohol (except client entertainment with approval)
- Gym memberships (separate wellness benefit)
- Personal subscriptions

Submission Process:
- Submit expenses within 30 days
- Attach itemized receipts for all expenses over $25
- Use Navan Expense app for easy submission
- Manager approval required for amounts over $500

Processing Time:
- Approved expenses reimbursed within 5 business days
- Direct deposit to your payroll account
- Questions? Contact accounts@company.com""",
        "source": "Finance",
        "tags": ["Expenses", "Finance", "Travel"]
    },
    {
        "title": "Onboarding Guide for New Engineers",
        "text": """Engineering Onboarding Checklist

Week 1 - Setup and Orientation:
[] Complete HR paperwork and I-9 verification
[] Set up laptop with IT support
[] Configure development environment
[] Get access to GitHub, Jira, and Slack
[] Complete security training
[] Meet your manager and team

Week 2 - Learning:
[] Review architecture documentation
[] Complete onboarding tickets (marked 'good-first-issue')
[] Pair program with assigned buddy
[] Attend team standup and planning meetings
[] Read through main codebase

Week 3-4 - Contributing:
[] Pick up first real ticket with support
[] Complete code review training
[] Set up on-call access (shadow only)
[] Create first pull request
[] Participate in code review

First 90 Days Goals:
[] Complete 10+ code contributions
[] Understand main system architecture
[] Complete all required training
[] Give and receive peer feedback
[] Set goals with manager

Resources:
- Engineering Wiki: wiki.internal/engineering
- Slack: #eng-help for questions
- Buddy: Your assigned mentor for first month
- Manager: Weekly 1:1 meetings

Don't hesitate to ask questions! Everyone wants you to succeed.""",
        "source": "Engineering",
        "tags": ["Onboarding", "Engineering", "New Hire"]
    },
    {
        "title": "Product Development Process",
        "text": """Product Development Lifecycle

Phase 1 - Discovery:
- Product manager defines problem statement
- User research and competitive analysis
- Technical feasibility assessment
- Create PRD (Product Requirements Document)

Phase 2 - Design:
- UX research and user flows
- Design mockups and prototypes
- Design review with stakeholders
- Technical design document
- Architecture review board approval

Phase 3 - Development:
- Break down into engineering tickets
- Sprint planning and estimation
- Two-week development sprints
- Daily standups and weekly demos
- Code review and testing

Phase 4 - Quality Assurance:
- Automated testing (unit, integration, e2e)
- Manual QA testing
- Performance testing
- Security review for sensitive features
- Accessibility audit

Phase 5 - Launch:
- Staged rollout (10% -> 50% -> 100%)
- Feature flags for controlled release
- Monitoring and alerting setup
- Documentation and training
- Customer communication

Phase 6 - Iterate:
- Monitor metrics and user feedback
- Bug fixes and improvements
- Plan next iteration
- Retrospective and learnings""",
        "source": "Product Team",
        "tags": ["Product", "Process", "Development"]
    },
    {
        "title": "Company Benefits Overview",
        "text": """Employee Benefits Package

Health Insurance:
- Medical: Choice of PPO or HDHP plans
- Dental: Delta Dental coverage
- Vision: VSP coverage
- Company pays 90% of employee premiums
- 70% coverage for dependents

Financial Benefits:
- 401(k) with 4% company match
- Annual bonus: 10-20% based on performance
- Equity: RSUs vest over 4 years
- Life insurance: 2x annual salary
- Short and long-term disability

Wellness:
- $100/month wellness stipend
- Free Headspace subscription
- Annual health screenings
- Employee assistance program

Family:
- 16 weeks paid parental leave
- Fertility benefits (up to $25,000)
- Dependent care FSA
- Back-up childcare program

Professional Development:
- $3,000 annual learning budget
- Conference attendance
- Internal training programs
- Mentorship opportunities

Perks:
- Flexible work arrangements
- $100/month remote work stipend
- Quarterly team events
- Annual company retreat
- Free lunch on office days

Questions? Contact benefits@company.com""",
        "source": "HR",
        "tags": ["Benefits", "HR", "Compensation"]
    },
    {
        "title": "API Documentation Standards",
        "text": """API Design and Documentation Standards

RESTful Design Principles:
- Use nouns for resources, not verbs
- Standard HTTP methods: GET, POST, PUT, PATCH, DELETE
- Consistent URL patterns: /api/v1/resources/{id}
- Use plural nouns: /users not /user
- Nest sub-resources logically: /users/{id}/orders

Response Format:
All API responses should follow this structure:
{
  "data": { ... },
  "meta": {
    "page": 1,
    "total": 100
  },
  "errors": []
}

HTTP Status Codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Server Error

Pagination:
- Use cursor-based pagination for large datasets
- Default page size: 20
- Maximum page size: 100
- Include 'next' and 'prev' links in response

Authentication:
- Use JWT tokens for API authentication
- Tokens expire after 24 hours
- Include in Authorization header: Bearer {token}

Rate Limiting:
- Standard limit: 1000 requests/hour
- Include rate limit headers in response
- Return 429 when limits exceeded

Documentation:
- All APIs documented in OpenAPI 3.0
- Auto-generated from code annotations
- Available at /api/docs""",
        "source": "Engineering",
        "tags": ["API", "Documentation", "Engineering"]
    },
]


async def seed_database():
    """Main function to seed the database with comprehensive test data."""
    print("🌱 Starting comprehensive database seeding...")
    
    await Database.connect()
    db = Database.get_db()
    
    # 1. Seed Skills Taxonomy
    print("\n📚 Seeding skills taxonomy...")
    await db.skills.delete_many({})
    for skill in SKILL_TAXONOMY:
        skill["created_at"] = datetime.utcnow()
        skill["updated_at"] = datetime.utcnow()
    await db.skills.insert_many(SKILL_TAXONOMY)
    print(f"✅ Inserted {len(SKILL_TAXONOMY)} skills with relationships")
    
    # 2. Seed Candidates
    print("\n👥 Seeding candidates...")
    await db.candidates.delete_many({})
    for candidate in CANDIDATES:
        candidate["user_id"] = candidate["email"].split("@")[0].replace(".", "_")
        candidate["created_at"] = datetime.utcnow()
        candidate["updated_at"] = datetime.utcnow()
        candidate["is_active"] = True
    await db.candidates.insert_many(CANDIDATES)
    print(f"✅ Inserted {len(CANDIDATES)} candidates with detailed profiles")
    
    # 3. Seed Jobs
    print("\n💼 Seeding jobs...")
    await db.jobs.delete_many({})
    for job in JOBS:
        job["created_at"] = datetime.utcnow()
        job["updated_at"] = datetime.utcnow()
        job["is_active"] = True
    await db.jobs.insert_many(JOBS)
    print(f"✅ Inserted {len(JOBS)} jobs with detailed descriptions")
    
    # 4. Seed Documents for RAG
    print("\n📄 Seeding documents for RAG...")
    await db.documents.delete_many({})
    for doc in DOCUMENTS:
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
    await db.documents.insert_many(DOCUMENTS)
    print(f"✅ Inserted {len(DOCUMENTS)} documents for Q&A")
    
    # 5. Clean up old chunks (will be regenerated during training)
    await db.doc_chunks.delete_many({})
    print("🧹 Cleaned up document chunks (will regenerate during training)")
    
    # Summary
    print("\n" + "="*50)
    print("✅ DATABASE SEEDING COMPLETE!")
    print("="*50)
    print(f"📊 Total skills: {len(SKILL_TAXONOMY)}")
    print(f"👥 Total candidates: {len(CANDIDATES)}")
    print(f"💼 Total jobs: {len(JOBS)}")
    print(f"📄 Total documents: {len(DOCUMENTS)}")
    print("\n🔄 Next steps:")
    print("1. Run the server: uvicorn app.main:app --reload")
    print("2. Train agents via API or UI")
    print("3. Test predictions!")
    
    await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_database())
