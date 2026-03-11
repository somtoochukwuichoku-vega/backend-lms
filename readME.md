# Learn-EZ: Multi-Tenant Learning Management System

Learn-EZ is a specialized backend for a Learning Management System built with Django and the Django Rest Framework. Unlike a standard online course platform, this system is designed around an **Organization** model, allowing multiple schools or companies to host their own private or public course catalogs on the same infrastructure.

## Core Project Philosophy

The project was built to solve the complexities of institutional learning. This means handling scenarios where a single user might be a student in one organization, an instructor in another, and an administrator in a third.

## Key Features

### 1. Multi-Tenant Organization Structure

The platform is centered on Organizations.

* **Access Control:** Organizations can be private (requiring admin approval) or public.
* **Role Hierarchy:** We use a ranked system (Admin > Instructor > Student) to resolve permissions. If a user is granted a temporary role via delegation, the system automatically calculates their "effective role" to ensure they always have the highest level of access they are entitled to.

### 2. The Course Engine

The academic structure is hierarchical: **Organization > Course > Module > Lesson.**

* **Flexible Payments:** Courses support one-time payments and automated installment plans.
* **Content Types:** Lessons support text-based content, video URLs, and direct video uploads.
* **Privacy:** Video content and specific lesson data are strictly protected. Even if an endpoint is public, the actual educational material is only served to enrolled students or the course instructor.

### 3. AI-Powered Automation

To assist instructors, I’ve integrated an AI pipeline for lesson processing:

* **Transcription:** Uses AssemblyAI to convert lesson videos into text transcripts.
* **Summarization:** Uses Groq (Llama 3.3) to condense transcripts into concise educational summaries.
* **Background Processing:** These tasks are handled asynchronously via `django-tasks` to ensure the API remains responsive while the AI is working in the background.

### 4. Financial Integration

Payments are handled through Stripe.

* **Webhooks:** The system listens for Stripe events to automatically enroll students once a payment is confirmed.
* **Installment Logic:** For users on payment plans, the system tracks "installments paid" vs "total installments," only fully unlocking specific certificate-level access once the balance is cleared.

### 5. Delegated Permissions

A unique feature of this project is the **Delegation** system. This allows an admin to grant "Temporary" instructor or admin status to a user. These delegations can be set to expire automatically or be revoked instantly, which is ideal for guest instructors or temporary staff.

## Technical Stack

* **Language:** Python 3.x
* **Framework:** Django with Django Rest Framework (DRF)
* **Database:** PostgreSQL
* **Storage:** Cloudinary (for images and video content)
* **Authentication:** JWT (SimpleJWT) for secure, stateless API access
* **Documentation:** Automated OpenAPI schema generation via Drf-Spectacular (accessible via Swagger UI)

## API Structure Overview

* **/api/v1/auth/**: Handles user registration, profile management, and JWT token lifecycle.
* **/api/v1/org/**: The heart of the multi-tenant logic. Used for managing memberships, join requests, and delegations.
* **/api/v1/courses/**: Handles the academic content, including the AI summary triggers.
* **/api/v1/payments/**: Interfaces with Stripe to initialize checkout sessions for courses and installments.

## How to Navigate the Codebase

* **academics/**: Contains the logic for courses, lessons, AI utilities, and enrollment.
* **users/**: Manages the custom User model and the Organization/Membership logic.
* **delegations/**: Contains the logic for temporary role elevation.
* **payments/**: Manages the transaction records and Stripe integration.
* **django_rest_api/settings.py**: Configuration for Cloudinary, Stripe, AssemblyAI, and Groq.


## Live Project Links
Production Backend API: https://backend-lms-lv7l.onrender.com/api/v1/

Live Frontend Application: https://learn-ez-frontend.vercel.app/

Admin Panel: https://backend-lms-lv7l.onrender.com/admin/

## You can use the test account to browse through the project 
Username:Klocwise
password:klocwise@

## API Documentation
The project includes interactive documentation generated via drf-spectacular:

Swagger UI (Interactive): https://backend-lms-lv7l.onrender.com/api/docs/swagger/

## Future Roadmap

I am looking to expand this system to include:

* Interactive Quizzes with automated grading.
* Certificate generation upon course completion using the progress tracking already in place.
* A notification system to alert admins of pending join requests or students of upcoming assignment deadlines.