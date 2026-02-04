"""
Machine Learning Model for Student Risk Prediction
Uses Object-Oriented Programming (OOP) design pattern
"""
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib


class StudentRiskPredictor:
    """
    Machine Learning model to predict student academic risk level.
    
    Uses Random Forest Classifier for multi-class classification.
    Risk levels: 'Low', 'Medium', 'High'
    
    Features:
        - attendance_percentage (0-100)
        - carry_mark_percentage (0-100)  
        - past_gpa (0-4.0)
    
    Example usage:
        predictor = StudentRiskPredictor()
        predictor.train_model()
        risk = predictor.predict_risk(85, 70, 3.2)
        print(risk)  # 'Low'
    """
    
    # Class constants
    MODEL_PATH = 'models/risk_model.pkl'
    SCALER_PATH = 'models/scaler.pkl'
    
    # Risk thresholds
    RISK_LABELS = ['Low', 'Medium', 'High']
    
    def __init__(self):
        """Initialize the predictor with model and scaler"""
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Try to load existing model
        self._load_model()
    
    def _generate_training_data(self, n_samples=1000):
        """
        Generate synthetic training data for the model.
        
        Creates realistic student data based on academic patterns:
        - High attendance + good marks = Low risk
        - Medium attendance or marks = Medium risk
        - Low attendance or poor marks = High risk
        
        Args:
            n_samples: Number of synthetic samples to generate
            
        Returns:
            DataFrame with features and labels
        """
        np.random.seed(42)
        
        data = []
        
        for _ in range(n_samples):
            # Generate random base values
            attendance = np.random.uniform(50, 100)
            carry_mark = np.random.uniform(20, 100)
            past_gpa = np.random.uniform(0.5, 4.0)
            
            # Determine risk based on rules
            risk_score = 0
            
            # Attendance rules
            if attendance < 70:
                risk_score += 2
            elif attendance < 80:
                risk_score += 1
            
            # Carry mark rules
            if carry_mark < 40:
                risk_score += 2
            elif carry_mark < 60:
                risk_score += 1
            
            # GPA rules
            if past_gpa < 2.0:
                risk_score += 2
            elif past_gpa < 2.5:
                risk_score += 1
            
            # Assign risk label
            if risk_score >= 4:
                risk = 'High'
            elif risk_score >= 2:
                risk = 'Medium'
            else:
                risk = 'Low'
            
            # Add some noise to make it realistic
            if np.random.random() < 0.1:
                # 10% chance of noise
                risk = np.random.choice(self.RISK_LABELS)
            
            data.append({
                'attendance': attendance,
                'carry_mark': carry_mark,
                'past_gpa': past_gpa,
                'risk': risk
            })
        
        return pd.DataFrame(data)
    
    def train_model(self, data=None):
        """
        Train the Random Forest model.
        
        Args:
            data: Optional DataFrame with training data.
                  If None, generates synthetic data.
        
        Returns:
            float: Model accuracy score
        """
        # Generate data if not provided
        if data is None:
            data = self._generate_training_data()
        
        # Prepare features and labels
        X = data[['attendance', 'carry_mark', 'past_gpa']]
        y = data['risk']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Calculate accuracy
        accuracy = self.model.score(X_test_scaled, y_test)
        
        self.is_trained = True
        
        # Save model
        self._save_model()
        
        print(f"✅ Model trained successfully! Accuracy: {accuracy:.2%}")
        return accuracy
    
    def predict_risk(self, attendance, carry_mark, past_gpa):
        """
        Predict student risk level.
        
        Args:
            attendance: Attendance percentage (0-100)
            carry_mark: Carry mark percentage (0-100)
            past_gpa: Past GPA (0-4.0)
            
        Returns:
            str: Risk level ('Low', 'Medium', or 'High')
        """
        if not self.is_trained:
            # Fallback to rule-based prediction
            return self._rule_based_prediction(attendance, carry_mark, past_gpa)
        
        # Prepare input
        features = np.array([[attendance, carry_mark, past_gpa]])
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        
        return prediction
    
    def predict_risk_proba(self, attendance, carry_mark, past_gpa):
        """
        Predict risk level with probability scores.
        
        Args:
            attendance: Attendance percentage (0-100)
            carry_mark: Carry mark percentage (0-100)  
            past_gpa: Past GPA (0-4.0)
            
        Returns:
            dict: Probability for each risk level
        """
        if not self.is_trained:
            risk = self._rule_based_prediction(attendance, carry_mark, past_gpa)
            return {
                'Low': 1.0 if risk == 'Low' else 0.0,
                'Medium': 1.0 if risk == 'Medium' else 0.0,
                'High': 1.0 if risk == 'High' else 0.0
            }
        
        features = np.array([[attendance, carry_mark, past_gpa]])
        features_scaled = self.scaler.transform(features)
        
        probabilities = self.model.predict_proba(features_scaled)[0]
        classes = self.model.classes_
        
        return dict(zip(classes, probabilities))
    
    def _rule_based_prediction(self, attendance, carry_mark, past_gpa):
        """
        Fallback rule-based prediction when model is not trained.
        
        Args:
            attendance: Attendance percentage
            carry_mark: Carry mark percentage
            past_gpa: Past GPA
            
        Returns:
            str: Risk level
        """
        risk_score = 0
        
        # Attendance check
        if attendance < 70:
            risk_score += 2
        elif attendance < 80:
            risk_score += 1
        
        # Carry mark check
        if carry_mark < 40:
            risk_score += 2
        elif carry_mark < 60:
            risk_score += 1
        
        # GPA check
        if past_gpa < 2.0:
            risk_score += 2
        elif past_gpa < 2.5:
            risk_score += 1
        
        # Determine risk
        if risk_score >= 4:
            return 'High'
        elif risk_score >= 2:
            return 'Medium'
        return 'Low'
    
    def get_study_recommendation(self, risk_level, weak_subjects=None):
        """
        Generate personalized study recommendations.
        
        Args:
            risk_level: Current risk level ('Low', 'Medium', 'High')
            weak_subjects: Optional list of weak subject names
            
        Returns:
            dict: Recommendations with study hours and advice
        """
        recommendations = {
            'risk_level': risk_level,
            'study_hours': 0,
            'advice': [],
            'priority': 'Normal',
            'resources': []
        }
        
        if risk_level == 'High':
            recommendations['study_hours'] = 6
            recommendations['priority'] = 'Urgent'
            recommendations['advice'] = [
                "⚠️ Your academic performance needs immediate attention.",
                "📚 Increase daily study hours to at least 6 hours.",
                "👨‍🏫 Consider getting a tutor or joining study groups.",
                "📅 Create a strict study schedule and follow it.",
                "🎯 Focus on understanding core concepts, not memorization.",
                "📝 Review past exams and practice problems daily."
            ]
            recommendations['resources'] = [
                {'name': 'NotebookLM', 'url': 'https://notebooklm.google.com/', 'desc': 'AI-powered study assistant'},
                {'name': 'Khan Academy', 'url': 'https://www.khanacademy.org/', 'desc': 'Free educational resources'},
                {'name': 'Coursera', 'url': 'https://www.coursera.org/', 'desc': 'University-level courses'}
            ]
            
        elif risk_level == 'Medium':
            recommendations['study_hours'] = 4
            recommendations['priority'] = 'Moderate'
            recommendations['advice'] = [
                "📊 You're doing okay, but there's room for improvement.",
                "📚 Aim for 4-5 hours of focused study daily.",
                "✅ Ensure 100% class attendance from now on.",
                "📝 Complete all assignments on time.",
                "🔄 Review notes within 24 hours of each lecture.",
                "💪 Don't let your guard down - stay consistent!"
            ]
            recommendations['resources'] = [
                {'name': 'Quizlet', 'url': 'https://quizlet.com/', 'desc': 'Flashcards for studying'},
                {'name': 'YouTube Edu', 'url': 'https://www.youtube.com/education', 'desc': 'Educational videos'}
            ]
            
        else:  # Low risk
            recommendations['study_hours'] = 2
            recommendations['priority'] = 'Maintain'
            recommendations['advice'] = [
                "🌟 Great job! Keep up the excellent work!",
                "📚 Maintain your current study habits (2-3 hours daily).",
                "🎯 Challenge yourself with advanced topics.",
                "👥 Consider helping classmates who are struggling.",
                "📖 Explore additional reading materials.",
                "🏆 Aim for Dean's List if you aren't already there!"
            ]
            recommendations['resources'] = [
                {'name': 'MIT OpenCourseWare', 'url': 'https://ocw.mit.edu/', 'desc': 'Advanced learning materials'},
                {'name': 'arXiv', 'url': 'https://arxiv.org/', 'desc': 'Research papers'}
            ]
        
        # Add subject-specific advice
        if weak_subjects:
            recommendations['weak_subjects'] = weak_subjects
            recommendations['advice'].append(
                f"🎯 Focus extra attention on: {', '.join(weak_subjects)}"
            )
        
        return recommendations
    
    def get_feature_importance(self):
        """
        Get feature importance scores from the trained model.
        
        Returns:
            dict: Feature names and their importance scores
        """
        if not self.is_trained or self.model is None:
            return {
                'attendance': 0.35,
                'carry_mark': 0.40,
                'past_gpa': 0.25
            }
        
        features = ['attendance', 'carry_mark', 'past_gpa']
        importances = self.model.feature_importances_
        
        return dict(zip(features, importances))
    
    def _save_model(self):
        """Save the trained model and scaler to disk"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
            
            joblib.dump(self.model, self.MODEL_PATH)
            joblib.dump(self.scaler, self.SCALER_PATH)
        except Exception as e:
            print(f"Warning: Could not save model: {e}")
    
    def _load_model(self):
        """Load the model and scaler from disk if available"""
        try:
            if os.path.exists(self.MODEL_PATH) and os.path.exists(self.SCALER_PATH):
                self.model = joblib.load(self.MODEL_PATH)
                self.scaler = joblib.load(self.SCALER_PATH)
                self.is_trained = True
                print("✅ Loaded existing ML model")
        except Exception as e:
            print(f"Note: No existing model found, will train new one: {e}")
            self.is_trained = False


class StudyAssistant:
    """
    AI-powered study assistant that provides personalized help.
    Combines ML predictions with rule-based recommendations.
    """
    
    def __init__(self):
        """Initialize the study assistant with risk predictor"""
        self.predictor = StudentRiskPredictor()
    
    def analyze_student(self, attendance_data, results_data, cgpa):
        """
        Perform comprehensive analysis of student performance.
        
        Args:
            attendance_data: List of attendance records
            results_data: List of result records
            cgpa: Current CGPA
            
        Returns:
            dict: Comprehensive analysis and recommendations
        """
        analysis = {
            'overall_status': 'Good',
            'risk_level': 'Low',
            'attendance_status': 'Good',
            'academic_status': 'Good',
            'weak_subjects': [],
            'recommendations': [],
            'statistics': {}
        }
        
        # Calculate average attendance
        if attendance_data:
            avg_attendance = sum(a.attendance_percentage for a in attendance_data) / len(attendance_data)
            analysis['statistics']['avg_attendance'] = avg_attendance
            
            if avg_attendance < 80:
                analysis['attendance_status'] = 'At Risk' if avg_attendance >= 70 else 'Critical'
        else:
            avg_attendance = 100  # Assume perfect if no data
            analysis['statistics']['avg_attendance'] = avg_attendance
        
        # Calculate average carry marks
        if results_data:
            avg_carry = sum(r.carry_percentage for r in results_data) / len(results_data)
            analysis['statistics']['avg_carry_mark'] = avg_carry
            
            # Find weak subjects
            for r in results_data:
                if r.carry_percentage < 50:
                    analysis['weak_subjects'].append(r.subject_name)
        else:
            avg_carry = 70  # Default
            analysis['statistics']['avg_carry_mark'] = avg_carry
        
        # Add CGPA
        analysis['statistics']['cgpa'] = cgpa
        
        # Predict risk
        risk = self.predictor.predict_risk(avg_attendance, avg_carry, cgpa)
        analysis['risk_level'] = risk
        
        # Get recommendations
        recs = self.predictor.get_study_recommendation(risk, analysis['weak_subjects'])
        analysis['recommendations'] = recs
        
        # Set overall status
        if risk == 'High':
            analysis['overall_status'] = 'Critical'
            analysis['academic_status'] = 'Needs Improvement'
        elif risk == 'Medium':
            analysis['overall_status'] = 'Moderate'
            analysis['academic_status'] = 'Average'
        else:
            analysis['overall_status'] = 'Good'
            analysis['academic_status'] = 'On Track'
        
        return analysis
    
    def get_quick_advice(self, question):
        """
        Provide quick advice based on common questions.
        
        Args:
            question: User's question string
            
        Returns:
            str: Advice response
        """
        question = question.lower()
        
        # Common questions and responses
        responses = {
            'attendance': "📊 To avoid being barred, maintain at least 80% attendance. Missing more than 20% of classes may result in examination bar.",
            'bar': "⚠️ Examination bar occurs when attendance falls below 80%. Calculate your current percentage and plan to attend all remaining classes.",
            'cgpa': "📈 CGPA is calculated as: Σ(Credit Hours × Grade Points) ÷ Σ(Credit Hours). Use the CGPA calculator to track your progress.",
            'grade': "📚 IIUM grading: A(80-100), A-(75-79), B+(70-74), B(65-69), B-(60-64), C+(55-59), C(50-54), D(45-49), D-(40-44), E(35-39), F(0-34)",
            'pass': "✅ To pass a subject, you need at least 35% in carry marks AND 35% in final exam. The total should be at least 50% (grade C).",
            'study': "📖 Effective study tips: 1) Review notes daily, 2) Practice past papers, 3) Form study groups, 4) Take regular breaks, 5) Stay consistent.",
            'exam': "📝 Final exam tips: 1) Start revising 2 weeks early, 2) Focus on weak topics, 3) Practice time management, 4) Get enough sleep before exam.",
            'stress': "💆 Feeling stressed? Try: 1) Deep breathing exercises, 2) Short walks, 3) Talk to friends/counselors, 4) Break tasks into smaller parts.",
            'help': "🆘 I can help with: attendance tracking, CGPA calculation, exam preparation, study tips, and academic planning. What do you need?"
        }
        
        # Find matching response
        for keyword, response in responses.items():
            if keyword in question:
                return response
        
        # Default response
        return "🤔 I'm here to help with your studies! Try asking about: attendance, CGPA, grades, studying, exams, or passing requirements."
