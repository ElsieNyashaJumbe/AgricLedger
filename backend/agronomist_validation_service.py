"""
Agronomist Validation Service for AgricLedger
Manages human expert agronomist validation cases and computes genuine expert agreement metrics.
"""

import os
import csv
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATION_TEMPLATE_PATH = os.path.join(BASE_DIR, 'data', 'validation', 'agronomist_validation_template.csv')
EVALUATIONS_LOG_PATH = os.path.join(BASE_DIR, 'data', 'validation', 'agronomist_evaluations_log.csv')


class AgronomistValidationService:
    """
    Service managing human expert validation cases, evaluation logging,
    and computing empirical Agreement / Precision / Recall / F1 metrics.
    """

    def __init__(self, template_path: str = VALIDATION_TEMPLATE_PATH, log_path: str = EVALUATIONS_LOG_PATH):
        self.template_path = template_path
        self.log_path = log_path
        self._ensure_files()

    def _ensure_files(self):
        """Ensures validation template and evaluation log files exist"""
        os.makedirs(os.path.dirname(self.template_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'case_id', 'expert_id', 'model_prediction', 'agronomist_prediction',
                    'validation_date', 'comments', 'is_match'
                ])

    def get_validation_cases(self, filter_unevaluated: bool = False) -> List[Dict[str, Any]]:
        """Fetch validation cases from template file"""
        if not os.path.exists(self.template_path):
            logger.warning(f"Validation template not found at {self.template_path}")
            return []

        df = pd.read_csv(self.template_path, keep_default_na=False)
        cases = df.to_dict('records')

        if filter_unevaluated:
            cases = [c for c in cases if not c.get('agronomist_prediction')]

        return cases

    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific validation case by case_id"""
        cases = self.get_validation_cases()
        for c in cases:
            if str(c.get('case_id')).lower() == str(case_id).lower():
                return c
        return None

    def submit_evaluation(self, case_id: str, agronomist_prediction: str, expert_id: str = "EXPERT-ZW-001", comments: str = "") -> Dict[str, Any]:
        """
        Record a genuine human expert evaluation for a specific case.

        Args:
            case_id: Target case identifier (e.g. VAL-ZW-001)
            agronomist_prediction: Expert recommendation ('Recommended', 'Not Recommended', 'Uncertain')
            expert_id: Anonymized expert identifier
            comments: Optional agronomic reasoning

        Returns:
            Dict containing submission result and updated agreement summary.
        """
        case = self.get_case_by_id(case_id)
        if not case:
            return {'success': False, 'error': f'Case ID {case_id} not found'}

        if agronomist_prediction not in ['Recommended', 'Not Recommended', 'Uncertain']:
            return {'success': False, 'error': 'Invalid prediction. Must be Recommended, Not Recommended, or Uncertain.'}

        model_pred = case.get('model_prediction', '')
        is_match = (model_pred == agronomist_prediction) if agronomist_prediction != 'Uncertain' else False
        val_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 1. Update template CSV
        df = pd.read_csv(self.template_path, keep_default_na=False)
        idx = df[df['case_id'] == case_id].index
        if len(idx) > 0:
            df.loc[idx[0], 'agronomist_prediction'] = agronomist_prediction
            df.loc[idx[0], 'validation_date'] = val_date
            df.loc[idx[0], 'comments'] = comments
            df.to_csv(self.template_path, index=False)

        # 2. Append to evaluations log
        with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([case_id, expert_id, model_pred, agronomist_prediction, val_date, comments, is_match])

        logger.info(f"✅ Submitted agronomist evaluation for {case_id}: Model='{model_pred}' vs Expert='{agronomist_prediction}'")

        metrics = self.calculate_metrics()
        return {
            'success': True,
            'message': f'Evaluation recorded for case {case_id}',
            'case_id': case_id,
            'agronomist_prediction': agronomist_prediction,
            'is_match': is_match,
            'agreement_metrics': metrics
        }

    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculates empirical Agreement Rate, Accuracy, Precision, Recall, F1, and Confusion Matrix
        across all submitted genuine human agronomist evaluations.
        """
        if not os.path.exists(self.template_path):
            return {'status': 'NO_DATA', 'agreement_pct': 0.0, 'total_evaluations': 0}

        df = pd.read_csv(self.template_path, keep_default_na=False)
        evaluated_df = df[df['agronomist_prediction'].str.strip() != ''].copy()

        total_evaluated = len(evaluated_df)
        if total_evaluated == 0:
            return {
                'status': 'GENUINE_EVALUATIONS_PENDING',
                'total_cases': len(df),
                'evaluated_cases': 0,
                'agreement_pct': 0.0,
                'objective_4_status': 'NOT YET ACHIEVED',
                'note': 'Template generated with blank expert labels. Genuine human agronomist evaluation pending.'
            }

        # Filter out Uncertain for strict binary metrics
        valid_binary_df = evaluated_df[evaluated_df['agronomist_prediction'].isin(['Recommended', 'Not Recommended'])]
        if len(valid_binary_df) == 0:
            return {
                'status': 'ONLY_UNCERTAIN_EVALUATIONS',
                'total_evaluated': total_evaluated,
                'agreement_pct': 0.0,
                'objective_4_status': 'NOT YET ACHIEVED'
            }

        matches = (valid_binary_df['model_prediction'] == valid_binary_df['agronomist_prediction']).sum()
        agreement_pct = round((matches / len(valid_binary_df)) * 100.0, 2)

        # Map to binary (1 = Recommended, 0 = Not Recommended)
        y_true = (valid_binary_df['agronomist_prediction'] == 'Recommended').astype(int)
        y_pred = (valid_binary_df['model_prediction'] == 'Recommended').astype(int)

        tp = int(((y_true == 1) & (y_pred == 1)).sum())
        tn = int(((y_true == 0) & (y_pred == 0)).sum())
        fp = int(((y_true == 0) & (y_pred == 1)).sum())
        fn = int(((y_true == 1) & (y_pred == 0)).sum())

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0
        accuracy = round((tp + tn) / len(valid_binary_df), 4)

        objective_4_achieved = (agreement_pct >= 75.0) and (len(valid_binary_df) >= 30)
        obj_4_status = 'ACHIEVED' if objective_4_achieved else 'NOT YET ACHIEVED'

        return {
            'status': 'EVALUATED',
            'total_cases_in_suite': len(df),
            'evaluated_cases': total_evaluated,
            'valid_binary_evaluations': len(valid_binary_df),
            'agronomist_matches': int(matches),
            'agreement_pct': agreement_pct,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': {'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn},
            'objective_4_target_pct': 75.0,
            'objective_4_status': obj_4_status
        }


# Singleton agronomist validation service
agronomist_validation_service = AgronomistValidationService()
