# Database Schema Design

## Overview
This document outlines the database schema design for the Assessment AI Application, detailing the tables, relationships, and key fields necessary to support all required functionality.

## User Management

### User
- **id**: Integer, Primary Key
- **username**: String, Unique
- **email**: String, Unique
- **password_hash**: String
- **role**: String (enum: 'admin', 'teacher')
- **first_name**: String
- **last_name**: String
- **created_at**: DateTime
- **updated_at**: DateTime
- **last_login**: DateTime
- **is_active**: Boolean

### UserProfile
- **id**: Integer, Primary Key
- **user_id**: Integer, Foreign Key (User)
- **profile_picture**: String (file path)
- **department**: String
- **bio**: Text
- **preferences**: JSON

## Assessment Management

### Category
- **id**: Integer, Primary Key
- **name**: String
- **description**: Text
- **created_by**: Integer, Foreign Key (User)
- **created_at**: DateTime
- **updated_at**: DateTime

### Module
- **id**: Integer, Primary Key
- **name**: String
- **code**: String
- **description**: Text
- **category_id**: Integer, Foreign Key (Category)
- **created_by**: Integer, Foreign Key (User)
- **created_at**: DateTime
- **updated_at**: DateTime

### AssessmentBrief
- **id**: Integer, Primary Key
- **title**: String
- **description**: Text
- **module_id**: Integer, Foreign Key (Module)
- **file_path**: String
- **created_by**: Integer, Foreign Key (User)
- **created_at**: DateTime
- **updated_at**: DateTime
- **is_active**: Boolean

### Rubric
- **id**: Integer, Primary Key
- **assessment_id**: Integer, Foreign Key (AssessmentBrief)
- **title**: String
- **description**: Text
- **file_path**: String
- **created_at**: DateTime
- **updated_at**: DateTime

### RubricCriteria
- **id**: Integer, Primary Key
- **rubric_id**: Integer, Foreign Key (Rubric)
- **name**: String
- **description**: Text
- **weight**: Float
- **max_score**: Float

### StudentWork
- **id**: Integer, Primary Key
- **assessment_id**: Integer, Foreign Key (AssessmentBrief)
- **student_name**: String
- **student_id**: String
- **file_path**: String
- **submission_date**: DateTime
- **urls**: JSON (array of URLs referenced in work)
- **status**: String (enum: 'submitted', 'marking', 'marked')
- **uploaded_by**: Integer, Foreign Key (User)

## Marking and Feedback

### Mark
- **id**: Integer, Primary Key
- **student_work_id**: Integer, Foreign Key (StudentWork)
- **total_score**: Float
- **percentage**: Float
- **marked_by_ai**: Boolean
- **verified_by_teacher**: Boolean
- **teacher_id**: Integer, Foreign Key (User), Nullable
- **created_at**: DateTime
- **updated_at**: DateTime

### CriteriaMark
- **id**: Integer, Primary Key
- **mark_id**: Integer, Foreign Key (Mark)
- **criteria_id**: Integer, Foreign Key (RubricCriteria)
- **score**: Float
- **comments**: Text

### Feedback
- **id**: Integer, Primary Key
- **mark_id**: Integer, Foreign Key (Mark)
- **general_comments**: Text
- **strengths**: Text
- **areas_for_improvement**: Text
- **recommendations**: Text
- **created_at**: DateTime
- **updated_at**: DateTime

## Analytics

### AnalyticsData
- **id**: Integer, Primary Key
- **assessment_id**: Integer, Foreign Key (AssessmentBrief)
- **data_type**: String
- **data**: JSON
- **created_at**: DateTime

### Recommendation
- **id**: Integer, Primary Key
- **assessment_id**: Integer, Foreign Key (AssessmentBrief)
- **module_id**: Integer, Foreign Key (Module)
- **recommendation_text**: Text
- **recommendation_type**: String
- **priority**: Integer
- **created_at**: DateTime

## Website Customization

### WebsiteSection
- **id**: Integer, Primary Key
- **name**: String
- **description**: Text
- **content**: JSON
- **position**: Integer
- **is_active**: Boolean
- **created_by**: Integer, Foreign Key (User)
- **created_at**: DateTime
- **updated_at**: DateTime

### Template
- **id**: Integer, Primary Key
- **name**: String
- **description**: Text
- **template_data**: JSON
- **is_active**: Boolean
- **created_at**: DateTime
- **updated_at**: DateTime

### PageLayout
- **id**: Integer, Primary Key
- **name**: String
- **description**: Text
- **sections**: JSON (array of section IDs and their positions)
- **created_by**: Integer, Foreign Key (User)
- **is_active**: Boolean
- **created_at**: DateTime
- **updated_at**: DateTime

## Relationships

1. **User to UserProfile**: One-to-One
2. **User to Category**: One-to-Many
3. **User to Module**: One-to-Many
4. **User to AssessmentBrief**: One-to-Many
5. **Category to Module**: One-to-Many
6. **Module to AssessmentBrief**: One-to-Many
7. **AssessmentBrief to Rubric**: One-to-One
8. **Rubric to RubricCriteria**: One-to-Many
9. **AssessmentBrief to StudentWork**: One-to-Many
10. **StudentWork to Mark**: One-to-One
11. **Mark to CriteriaMark**: One-to-Many
12. **Mark to Feedback**: One-to-One
13. **AssessmentBrief to AnalyticsData**: One-to-Many
14. **AssessmentBrief to Recommendation**: One-to-Many
15. **Module to Recommendation**: One-to-Many
16. **User to WebsiteSection**: One-to-Many
17. **User to PageLayout**: One-to-Many

## Indexes

1. User(username, email)
2. Category(name)
3. Module(code)
4. AssessmentBrief(module_id)
5. StudentWork(assessment_id, student_id)
6. Mark(student_work_id)
7. AnalyticsData(assessment_id, data_type)
8. Recommendation(assessment_id, module_id)

## Notes

- JSON fields are used for flexible data structures like preferences, URLs, and template data
- Timestamps (created_at, updated_at) are included for auditing and tracking purposes
- Foreign keys maintain referential integrity
- Enums are used for fields with a fixed set of possible values
- Boolean flags indicate status (is_active, verified_by_teacher, etc.)
