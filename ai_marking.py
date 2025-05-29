"""
AI marking and feedback algorithms for assessment management.
"""

import os
import re
import json
import nltk
import numpy as np
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Initialize NLP components
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_md')
except:
    os.system('python -m spacy download en_core_web_md')
    nlp = spacy.load('en_core_web_md')


class AssessmentAI:
    """Main class for AI-powered assessment marking and feedback generation."""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(stop_words='english')
    
    def process_assessment_brief(self, brief_text):
        """
        Process assessment brief to extract key requirements and expectations.
        
        Args:
            brief_text (str): The text content of the assessment brief
            
        Returns:
            dict: Structured representation of the assessment brief
        """
        doc = nlp(brief_text)
        
        # Extract key information
        requirements = []
        learning_outcomes = []
        submission_details = []
        
        # Simple rule-based extraction (to be enhanced)
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            # Look for requirements
            if re.search(r'(must|should|need to|required to|expected to)', sent_text, re.IGNORECASE):
                requirements.append(sent_text)
            
            # Look for learning outcomes
            if re.search(r'(learning outcome|will be able to|demonstrate|understand|apply)', sent_text, re.IGNORECASE):
                learning_outcomes.append(sent_text)
            
            # Look for submission details
            if re.search(r'(submit|submission|deadline|due date|format|word count)', sent_text, re.IGNORECASE):
                submission_details.append(sent_text)
        
        # Extract key topics using noun chunks
        topics = [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) > 1]
        topics = list(set([topic.lower() for topic in topics if len(topic) > 5]))[:10]  # Top 10 unique topics
        
        return {
            'requirements': requirements,
            'learning_outcomes': learning_outcomes,
            'submission_details': submission_details,
            'key_topics': topics,
            'full_text': brief_text
        }
    
    def process_rubric(self, rubric_text):
        """
        Process rubric to extract marking criteria and expectations.
        
        Args:
            rubric_text (str): The text content of the rubric
            
        Returns:
            dict: Structured representation of the rubric
        """
        doc = nlp(rubric_text)
        
        # Extract criteria using regex patterns first
        criteria = []
        
        # Pattern for criteria with percentages: "Content (40%):"
        percentage_pattern = r'([A-Za-z\s]+)\s*\((\d+)%\):(.+?)(?=[A-Za-z\s]+\s*\(\d+%\):|Grade [A-F]:|$)'
        matches = re.findall(percentage_pattern, rubric_text, re.DOTALL)
        
        for name, weight, description in matches:
            criteria.append({
                'name': name.strip(),
                'weight': int(weight),
                'description': description.strip(),
                'keywords': self._extract_keywords(description.strip())
            })
        
        # If no criteria found with regex, try alternative approach
        if not criteria:
            # Extract criteria sections based on line breaks and formatting
            current_criterion = None
            current_description = []
            
            for para in rubric_text.split('\n\n'):
                para = para.strip()
                if not para:
                    continue
                    
                # Check if this looks like a criterion header
                if len(para.split()) <= 10 and (para.endswith(':') or para.endswith(')')):
                    # Save previous criterion if exists
                    if current_criterion:
                        criteria.append({
                            'name': current_criterion,
                            'description': ' '.join(current_description),
                            'keywords': self._extract_keywords(' '.join(current_description)),
                            'weight': 25  # Default equal weight if not specified
                        })
                    
                    current_criterion = para.rstrip(':)')
                    current_description = []
                else:
                    if current_criterion:
                        current_description.append(para)
            
            # Add the last criterion
            if current_criterion:
                criteria.append({
                    'name': current_criterion,
                    'description': ' '.join(current_description),
                    'keywords': self._extract_keywords(' '.join(current_description)),
                    'weight': 25  # Default equal weight if not specified
                })
        
        # If still no criteria found, create default ones
        if not criteria:
            # Create default criteria based on common assessment areas
            default_criteria = [
                {
                    'name': 'Content',
                    'weight': 40,
                    'description': 'Quality and comprehensiveness of content',
                    'keywords': ['content', 'quality', 'comprehensive', 'understanding', 'knowledge']
                },
                {
                    'name': 'Structure',
                    'weight': 30,
                    'description': 'Organization and logical flow',
                    'keywords': ['structure', 'organization', 'flow', 'coherent', 'logical']
                },
                {
                    'name': 'Research',
                    'weight': 20,
                    'description': 'Use of sources and evidence',
                    'keywords': ['research', 'sources', 'evidence', 'references', 'citation']
                },
                {
                    'name': 'Language',
                    'weight': 10,
                    'description': 'Grammar, spelling, and academic writing style',
                    'keywords': ['language', 'grammar', 'spelling', 'writing', 'style']
                }
            ]
            criteria = default_criteria
        
        # Extract grade boundaries if present
        grade_boundaries = self._extract_grade_boundaries(rubric_text)
        
        return {
            'criteria': criteria,
            'grade_boundaries': grade_boundaries,
            'full_text': rubric_text
        }
    
    def _extract_keywords(self, text):
        """Extract important keywords from text."""
        doc = nlp(text)
        keywords = []
        
        # Extract named entities
        for ent in doc.ents:
            keywords.append(ent.text.lower())
        
        # Extract important noun phrases
        for chunk in doc.noun_chunks:
            if chunk.root.pos_ in ['NOUN', 'PROPN'] and chunk.root.is_alpha:
                if chunk.root.text.lower() not in self.stop_words:
                    keywords.append(chunk.text.lower())
        
        # Extract important verbs
        for token in doc:
            if token.pos_ == 'VERB' and token.is_alpha and token.text.lower() not in self.stop_words:
                keywords.append(token.text.lower())
        
        # Remove duplicates and sort by length (longer phrases first)
        keywords = list(set(keywords))
        keywords.sort(key=len, reverse=True)
        
        return keywords[:20]  # Return top 20 keywords
    
    def _extract_grade_boundaries(self, text):
        """Extract grade boundaries from rubric text."""
        grade_patterns = {
            'A': r'(?:Grade|Mark)\s*A:?\s*(\d+)(?:\s*-\s*(\d+))?',
            'B': r'(?:Grade|Mark)\s*B:?\s*(\d+)(?:\s*-\s*(\d+))?',
            'C': r'(?:Grade|Mark)\s*C:?\s*(\d+)(?:\s*-\s*(\d+))?',
            'D': r'(?:Grade|Mark)\s*D:?\s*(\d+)(?:\s*-\s*(\d+))?',
            'F': r'(?:Grade|Mark)\s*F:?\s*(\d+)(?:\s*-\s*(\d+))?',
            'Fail': r'(?:Grade|Mark)\s*Fail:?\s*(\d+)(?:\s*-\s*(\d+))?',
            'Pass': r'(?:Grade|Mark)\s*Pass:?\s*(\d+)(?:\s*-\s*(\d+))?',
            'Merit': r'(?:Grade|Mark)\s*Merit:?\s*(\d+)(?:\s*-\s*(\d+))?',
            'Distinction': r'(?:Grade|Mark)\s*Distinction:?\s*(\d+)(?:\s*-\s*(\d+))?'
        }
        
        boundaries = {}
        
        for grade, pattern in grade_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(2):  # Range found
                    boundaries[grade] = (int(match.group(1)), int(match.group(2)))
                else:  # Single value found
                    boundaries[grade] = (int(match.group(1)), int(match.group(1)))
        
        # If no explicit boundaries found, try to infer from percentage mentions
        if not boundaries:
            percentage_pattern = r'(\d{1,2})\s*(?:-|to)\s*(\d{1,2})%?\s*(?:=|:)?\s*([A-Za-z]+)'
            for match in re.finditer(percentage_pattern, text):
                grade = match.group(3).strip()
                boundaries[grade] = (int(match.group(1)), int(match.group(2)))
        
        return boundaries
    
    def extract_urls(self, text):
        """
        Extract and validate URLs from student work.
        
        Args:
            text (str): The text content of student work
            
        Returns:
            list: List of valid URLs found in the text
        """
        # More comprehensive URL regex pattern that includes paths
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w./%?&=+#]*)?'
        
        # Find all URLs
        urls = re.findall(url_pattern, text)
        valid_urls = []
        
        for url in urls:
            try:
                # Parse URL to validate
                parsed_url = urlparse(url)
                if parsed_url.scheme and parsed_url.netloc:
                    valid_urls.append(url)
            except:
                continue
        
        return valid_urls
    
    def analyze_url_content(self, url):
        """
        Analyze content from a URL.
        
        Args:
            url (str): URL to analyze
            
        Returns:
            dict: Analysis of URL content or None if failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else "No title"
            
            # Extract main content (simplified)
            content = ""
            for para in soup.find_all('p'):
                content += para.get_text() + " "
            
            # Extract metadata
            meta_description = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag:
                meta_description = meta_tag.get('content', '')
            
            # Process with NLP
            if content:
                doc = nlp(content[:5000])  # Limit to first 5000 chars for performance
                
                # Extract key phrases
                key_phrases = [chunk.text for chunk in doc.noun_chunks 
                              if len(chunk.text.split()) > 1][:10]
                
                # Extract named entities
                entities = [(ent.text, ent.label_) for ent in doc.ents][:10]
                
                return {
                    'url': url,
                    'title': title,
                    'meta_description': meta_description,
                    'key_phrases': key_phrases,
                    'entities': entities,
                    'content_sample': content[:500] + "..." if len(content) > 500 else content
                }
            
            return {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'content_sample': content[:500] + "..." if len(content) > 500 else content
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'status': 'failed'
            }
    
    def mark_student_work(self, student_work_text, brief_analysis, rubric_analysis):
        """
        Mark student work based on assessment brief and rubric.
        
        Args:
            student_work_text (str): The text content of student work
            brief_analysis (dict): Processed assessment brief
            rubric_analysis (dict): Processed rubric
            
        Returns:
            dict: Marking results with scores and feedback
        """
        # Extract URLs for separate analysis
        urls = self.extract_urls(student_work_text)
        url_analyses = []
        
        for url in urls[:5]:  # Limit to first 5 URLs for performance
            url_analysis = self.analyze_url_content(url)
            if url_analysis:
                url_analyses.append(url_analysis)
        
        # Process student work with NLP
        doc = nlp(student_work_text)
        
        # Calculate text statistics
        word_count = len([token for token in doc if token.is_alpha])
        sentence_count = len(list(doc.sents))
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Extract key topics from student work
        student_topics = [chunk.text.lower() for chunk in doc.noun_chunks 
                         if len(chunk.text.split()) > 1 and chunk.root.pos_ in ['NOUN', 'PROPN']]
        
        # Compare with brief topics
        brief_topics = brief_analysis.get('key_topics', [])
        topic_coverage = self._calculate_topic_coverage(student_topics, brief_topics)
        
        # Evaluate against each criterion
        criteria_marks = []
        total_score = 0
        max_score = 0
        
        for criterion in rubric_analysis.get('criteria', []):
            criterion_name = criterion['name']
            criterion_keywords = criterion.get('keywords', [])
            
            # Calculate relevance score for this criterion
            relevance_score = self._calculate_criterion_relevance(doc, criterion_keywords)
            
            # Assign a score (simplified version - to be enhanced)
            # Assuming each criterion has equal weight and max score of 10
            criterion_max_score = 10
            criterion_score = round(relevance_score * criterion_max_score)
            
            # Generate feedback for this criterion
            criterion_feedback = self._generate_criterion_feedback(
                criterion_name, 
                criterion_score, 
                criterion_max_score,
                student_work_text,
                criterion.get('description', '')
            )
            
            criteria_marks.append({
                'name': criterion_name,
                'score': criterion_score,
                'max_score': criterion_max_score,
                'feedback': criterion_feedback
            })
            
            total_score += criterion_score
            max_score += criterion_max_score
        
        # Calculate percentage
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Determine grade based on boundaries
        grade = self._determine_grade(percentage, rubric_analysis.get('grade_boundaries', {}))
        
        # Generate overall feedback
        feedback = self._generate_overall_feedback(
            criteria_marks, 
            percentage, 
            grade, 
            topic_coverage,
            url_analyses
        )
        
        return {
            'total_score': total_score,
            'max_score': max_score,
            'percentage': percentage,
            'grade': grade,
            'criteria_marks': criteria_marks,
            'feedback': feedback,
            'statistics': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_sentence_length': avg_sentence_length,
                'url_count': len(urls),
                'topic_coverage': topic_coverage
            },
            'url_analyses': url_analyses
        }
    
    def _calculate_topic_coverage(self, student_topics, brief_topics):
        """Calculate how well student work covers topics from the brief."""
        if not brief_topics:
            return 1.0  # No topics to cover
        
        covered_topics = 0
        
        for brief_topic in brief_topics:
            for student_topic in student_topics:
                # Check if brief topic is contained in student topic or vice versa
                if brief_topic in student_topic or student_topic in brief_topic:
                    covered_topics += 1
                    break
                
                # Check similarity using spaCy
                brief_doc = nlp(brief_topic)
                student_doc = nlp(student_topic)
                similarity = brief_doc.similarity(student_doc)
                
                if similarity > 0.7:  # Threshold for considering topics similar
                    covered_topics += 1
                    break
        
        return covered_topics / len(brief_topics)
    
    def _calculate_criterion_relevance(self, doc, criterion_keywords):
        """Calculate relevance score for a criterion based on keyword presence."""
        if not criterion_keywords:
            return 0.5  # Default middle score if no keywords
        
        text = doc.text.lower()
        keyword_count = 0
        
        for keyword in criterion_keywords:
            if keyword.lower() in text:
                keyword_count += 1
        
        # Calculate relevance as proportion of keywords found
        relevance = keyword_count / len(criterion_keywords) if criterion_keywords else 0
        
        # Ensure score is between 0.3 and 0.9 to avoid extremes
        return min(0.9, max(0.3, relevance))
    
    def _generate_criterion_feedback(self, criterion_name, score, max_score, student_text, criterion_description):
        """Generate feedback for a specific criterion."""
        percentage = (score / max_score) * 100
        
        # Determine feedback type based on score
        if percentage >= 80:
            strength = "Excellent demonstration of " + criterion_name.lower()
            weakness = None
        elif percentage >= 60:
            strength = "Good demonstration of " + criterion_name.lower()
            weakness = "Could further improve " + criterion_name.lower() + " by providing more depth"
        elif percentage >= 40:
            strength = "Adequate demonstration of " + criterion_name.lower()
            weakness = "Need to develop " + criterion_name.lower() + " more thoroughly"
        else:
            strength = None
            weakness = "Significant improvement needed in " + criterion_name.lower()
        
        return {
            'strength': strength,
            'weakness': weakness,
            'suggestions': "Consider reviewing the requirements for " + criterion_name.lower() + " in the assessment brief"
        }
    
    def _determine_grade(self, percentage, grade_boundaries):
        """Determine grade based on percentage and grade boundaries."""
        # Default grade boundaries if none provided
        default_boundaries = {
            'A': (80, 100),
            'B': (70, 79),
            'C': (60, 69),
            'D': (50, 59),
            'F': (0, 49)
        }
        
        boundaries = grade_boundaries if grade_boundaries else default_boundaries
        
        for grade, (lower, upper) in boundaries.items():
            if lower <= percentage <= upper:
                return grade
        
        # Fallback logic if no matching boundary found
        if percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 60:
            return 'C'
        elif percentage >= 50:
            return 'D'
        else:
            return 'F'
    
    def _generate_overall_feedback(self, criteria_marks, percentage, grade, topic_coverage, url_analyses):
        """Generate overall feedback based on marking results."""
        # Collect strengths and areas for improvement
        strengths = []
        areas_for_improvement = []
        
        for criterion in criteria_marks:
            if criterion['feedback']['strength']:
                strengths.append(criterion['feedback']['strength'])
            
            if criterion['feedback']['weakness']:
                areas_for_improvement.append(criterion['feedback']['weakness'])
        
        # Generate general comments
        if percentage >= 80:
            general_comments = "Excellent work that demonstrates a comprehensive understanding of the subject matter."
        elif percentage >= 70:
            general_comments = "Very good work that shows a solid understanding of the subject matter."
        elif percentage >= 60:
            general_comments = "Good work that demonstrates understanding of most key aspects of the subject matter."
        elif percentage >= 50:
            general_comments = "Satisfactory work that meets the basic requirements but lacks depth in some areas."
        else:
            general_comments = "This work does not meet the minimum requirements and needs significant improvement."
        
        # Add comments about topic coverage
        if topic_coverage > 0.8:
            general_comments += " The work covers all key topics effectively."
        elif topic_coverage > 0.6:
            general_comments += " The work covers most key topics but could be more comprehensive."
        else:
            general_comments += " The work misses several key topics that should be addressed."
        
        # Add comments about URL usage if applicable
        if url_analyses:
            general_comments += f" The work incorporates {len(url_analyses)} external sources, which adds to its depth."
        
        # Generate recommendations
        recommendations = [
            "Review the assessment brief to ensure all requirements are met",
            "Consider the feedback for each criterion to improve future work"
        ]
        
        if areas_for_improvement:
            recommendations.append("Focus on addressing the identified areas for improvement")
        
        return {
            'general_comments': general_comments,
            'strengths': strengths,
            'areas_for_improvement': areas_for_improvement,
            'recommendations': recommendations
        }
    
    def generate_analytics(self, marking_results):
        """
        Generate analytics based on multiple marking results.
        
        Args:
            marking_results (list): List of marking results
            
        Returns:
            dict: Analytics data
        """
        if not marking_results:
            return {'error': 'No marking results provided'}
        
        # Calculate average scores
        total_percentages = [result['percentage'] for result in marking_results]
        avg_percentage = sum(total_percentages) / len(total_percentages)
        
        # Calculate grade distribution
        grades = [result.get('grade', 'N/A') for result in marking_results]
        grade_distribution = {}
        for grade in grades:
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        # Calculate criteria averages
        criteria_averages = {}
        for result in marking_results:
            for criterion in result.get('criteria_marks', []):
                name = criterion['name']
                score = criterion['score']
                max_score = criterion['max_score']
                percentage = (score / max_score) * 100 if max_score > 0 else 0
                
                if name not in criteria_averages:
                    criteria_averages[name] = []
                
                criteria_averages[name].append(percentage)
        
        # Calculate average for each criterion
        for name, scores in criteria_averages.items():
            criteria_averages[name] = sum(scores) / len(scores)
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for name, avg in criteria_averages.items():
            if avg >= 70:
                strengths.append(name)
            elif avg <= 50:
                weaknesses.append(name)
        
        # Calculate word count statistics
        word_counts = [result.get('statistics', {}).get('word_count', 0) for result in marking_results]
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        min_word_count = min(word_counts) if word_counts else 0
        max_word_count = max(word_counts) if word_counts else 0
        
        # Calculate URL usage statistics
        url_counts = [result.get('statistics', {}).get('url_count', 0) for result in marking_results]
        avg_url_count = sum(url_counts) / len(url_counts) if url_counts else 0
        
        return {
            'summary': {
                'count': len(marking_results),
                'avg_percentage': avg_percentage,
                'grade_distribution': grade_distribution
            },
            'criteria_analysis': {
                'averages': criteria_averages,
                'strengths': strengths,
                'weaknesses': weaknesses
            },
            'statistics': {
                'word_count': {
                    'average': avg_word_count,
                    'minimum': min_word_count,
                    'maximum': max_word_count
                },
                'url_usage': {
                    'average': avg_url_count
                }
            }
        }
    
    def generate_recommendations(self, analytics):
        """
        Generate recommendations based on analytics.
        
        Args:
            analytics (dict): Analytics data
            
        Returns:
            list: List of recommendations
        """
        recommendations = []
        
        # Check if analytics is valid
        if not analytics or 'error' in analytics:
            return [{'text': 'Not enough data to generate recommendations', 'type': 'general', 'priority': 'low'}]
        
        # Get key analytics data
        criteria_analysis = analytics.get('criteria_analysis', {})
        weaknesses = criteria_analysis.get('weaknesses', [])
        strengths = criteria_analysis.get('strengths', [])
        criteria_averages = criteria_analysis.get('averages', {})
        
        # Recommendations based on weak criteria
        for weakness in weaknesses:
            recommendations.append({
                'text': f"Consider revising teaching materials related to '{weakness}' as students are scoring lower in this area",
                'type': 'content',
                'priority': 'high'
            })
        
        # Recommendations based on overall performance
        avg_percentage = analytics.get('summary', {}).get('avg_percentage', 0)
        if avg_percentage < 60:
            recommendations.append({
                'text': "Overall student performance is below expectations. Consider reviewing the assessment brief for clarity and providing additional support materials",
                'type': 'assessment',
                'priority': 'high'
            })
        elif avg_percentage > 80:
            recommendations.append({
                'text': "Students are performing exceptionally well. Consider increasing the challenge level in future assessments",
                'type': 'assessment',
                'priority': 'medium'
            })
        
        # Recommendations based on word count
        avg_word_count = analytics.get('statistics', {}).get('word_count', {}).get('average', 0)
        if avg_word_count < 500:
            recommendations.append({
                'text': "Student submissions are quite brief. Consider providing clearer guidelines on expected depth and detail",
                'type': 'guidance',
                'priority': 'medium'
            })
        
        # Recommendations based on URL usage
        avg_url_count = analytics.get('statistics', {}).get('url_usage', {}).get('average', 0)
        if avg_url_count < 2:
            recommendations.append({
                'text': "Students are using few external sources. Consider emphasizing the importance of research and citation",
                'type': 'guidance',
                'priority': 'medium'
            })
        
        # General recommendations
        recommendations.append({
            'text': "Provide more example work to help students understand expectations",
            'type': 'guidance',
            'priority': 'low'
        })
        
        recommendations.append({
            'text': "Consider peer review activities to help students understand assessment criteria",
            'type': 'activity',
            'priority': 'medium'
        })
        
        return recommendations
