# Automated Compliance Checker for Legal Metrology 📜

## Project Overview
With the exponential growth of e-commerce, ensuring that product listings comply with the **Legal Metrology (Packaged Commodities) Rules, 2011** has become a significant challenge for regulatory bodies.  

Manual verification is inefficient and unscalable, leading to widespread non-compliance that compromises consumer protection.  

This project is an **AI-powered automated compliance checker** designed to continuously monitor e-commerce platforms like **Blinkit, Amazon, and Flipkart** in real-time.  

By shifting from a reactive, complaint-driven system to a proactive, technology-driven model, our solution ensures that **mandatory declarations** (e.g., MRP, *best before* date, country of origin) are accurately displayed, protecting over **250 million online shoppers in India**.

<img width="1919" height="762" alt="Screenshot 2025-09-24 073135" src="https://github.com/user-attachments/assets/c3dc985b-ed6a-4865-944b-b81d0e2219da" />
<img width="1878" height="915" alt="Screenshot 2025-09-24 073205" src="https://github.com/user-attachments/assets/40f883d1-0994-42bf-918b-540f6b3f383d" />
<img width="1919" height="997" alt="Screenshot 2025-09-24 073247" src="https://github.com/user-attachments/assets/325aa81e-fb94-4f9d-ae94-52bdb0ee38c5" />
<img width="1898" height="934" alt="Screenshot 2025-09-24 073331" src="https://github.com/user-attachments/assets/39eb5b68-5bc8-446a-a291-a20ab107b4e7" />
<img width="1905" height="496" alt="Screenshot 2025-09-24 073417" src="https://github.com/user-attachments/assets/a4b76dd2-cb8c-46c3-aeaa-d54c2cbd0163" />

---

## ✨ Key Features
Our solution offers a unique and robust approach to digital compliance:

- **Proactive & Real-Time Validation**  
  Continuously monitors thousands of product listings to flag violations as they happen, moving beyond manual spot-checks.

- **Multi-Language OCR for the Indian Market**  
  Utilizes advanced OCR to extract key details (MRP, FSSAI, Best Before) directly from product images in multiple Indian languages.

- **Scalable Cloud Architecture**  
  Built on a serverless, cloud-native foundation to reliably handle millions of listings across India, ensuring a nationally consistent enforcement tool.

- **Cross-Platform Compliance Scoring**  
  Establishes unified, data-driven benchmarks to identify non-compliant patterns and repeat offenders across the entire e-commerce industry.

- **Adaptive Rule Engine**  
  A flexible system that can be quickly updated to reflect changes in Legal Metrology and Consumer Protection regulations without requiring a major code overhaul.

- **Seamless Government Integration**  
  Designed for API-based cross-validation with government portals like **e-Maap** to verify the authenticity of FSSAI codes and manufacturer details.

---

## 🏗️ System Architecture and Workflow
The system is designed as a **distributed, four-layer architecture** to ensure scalability and efficiency.

1. **Data Acquisition Layer**  
   - The user selects a target website and a product range to scan from the web dashboard.  
   - This triggers multiple parallel compute devices (EC2 Instances, PCs, etc.) to begin scraping product data (titles, descriptions, images) to avoid rate-limiting.

2. **Processing Layer**  
   - Scraped product images are uploaded and stored in a central **Amazon S3 bucket**.  
   - An **AWS Lambda function** is automatically triggered on each image upload.  
   - This function uses an OCR model (**EasyOCR with AWS Textract fallback**) to extract text from the product label.  
   - Components:  
     - S3 Bucket for Images  
     - Lambda Function for OCR Processing  

3. **Compliance Validation Layer**  
   - The extracted text is saved to a **DynamoDB database**.  
   - A rule engine validates this data against Legal Metrology requirements and cross-references it with government databases to check for authenticity (e.g., FSSAI code).  
   - Component: DynamoDB Table with Compliance Data  

4. **Reporting & Dashboard Layer**  
   - A web-based dashboard, built with **Next.js**, provides regulators with a comprehensive view of compliance data.  
   - Features:  
     - Real-time compliance score  
     - Trends by category or seller  
     - Export of detailed violation reports  
   - Component: Product Compliance Summary Dashboard  

## Frontend Link: https://github.com/Kanishk2Kumar/e-commerce-compliance-checker
<img width="1919" height="1139" alt="Screenshot 2025-09-24 074150" src="https://github.com/user-attachments/assets/63f4567d-819c-4106-ae5a-42cd80981e8d" />
<img width="1919" height="1100" alt="Screenshot 2025-09-24 074228" src="https://github.com/user-attachments/assets/6eee987e-5f26-4f05-908f-0c8fb1160d09" />

---

## 🛠️ Tech Stack
| Category         | Technology |
|------------------|------------|
| **Frontend**     | Next.js, React, Tailwind CSS |
| **Cloud & Backend** | AWS (EC2, S3, Lambda, DynamoDB, IAM) |
| **Web Scraping** | Playwright, Headless Browsers |
| **AI / OCR**     | EasyOCR, AWS Textract |
| **Database**     | Amazon DynamoDB (NoSQL) |

---

## 🚧 Potential Challenges and Mitigation Strategies
| Challenge | Mitigation Strategy |
|-----------|----------------------|
| **Resistance from Platforms** | Use rotating proxies and multiple distributed EC2 instances to bypass detection. Mandate compliance via government directive. |
| **Dynamic Website UI** | Employ adaptive crawlers and headless browsers that can be updated automatically to handle frequent UI changes. |
| **Poor Image Quality** | Use a hybrid OCR model, combining EasyOCR with AWS Textract as fallback to improve accuracy on low-resolution images. |
| **High Data Volume & Cost** | Leverage serverless architecture (Lambda, S3) and auto-scaling cloud resources to manage costs and handle millions of SKUs efficiently. |
| **Legal/Ethical Concerns** | Only extract publicly available information and adhere strictly to government data usage and privacy policies. |

---

## 📈 Impact and Benefits
- **Protects Consumers**: Shields millions of online shoppers from misleading information like fake labels and incorrect MRPs, building trust in digital commerce.  
- **Boosts Economic Efficiency**: Reduces the cost of manual inspections by an estimated 50–60%, saving crores in litigation and penalties.  
- **Ensures Fair Market Practices**: Creates a level playing field by applying the same compliance rules to all sellers, big or small.  
- **Empowers Regulators**: Saves an estimated 60–70% of manual audit time for over 10,000 consumer protection officers, enabling data-driven enforcement.  
