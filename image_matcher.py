import cv2
import numpy as np
from dataclasses import dataclass
import logging
from pathlib import Path

@dataclass
class MatchQuality:
    structural_similarity: float
    edge_similarity: float
    histogram_similarity: float

@dataclass
class Match:
    center_x: int
    center_y: int
    confidence: float
    quality: MatchQuality

class ImageMatcher:
    def __init__(self, threshold=0.8, debug=False):
        self.threshold = threshold
        self.debug = debug
        
        # Set up logging
        self.logger = logging.getLogger('image_matcher')
        if debug:
            self.logger.setLevel(logging.DEBUG)
            
            # Create debug directory
            self.debug_dir = Path('temp/debug')
            self.debug_dir.mkdir(parents=True, exist_ok=True)

    def find_template(self, image, template, threshold=None):
        """Find a template in an image using template matching."""
        if threshold is None:
            threshold = self.threshold
            
        try:
            # Convert PIL Image to cv2 format if needed
            if not isinstance(image, np.ndarray):
                image = np.array(image)
            if not isinstance(template, np.ndarray):
                template = np.array(template)
            
            # Convert to BGR if needed
            if len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            if len(template.shape) == 3 and template.shape[2] == 4:
                template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
            
            # Template matching
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Get region for quality calculation
                h, w = template.shape[:2]
                region = image[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w]
                
                # Calculate quality metrics
                quality = self._calculate_quality(region, template)
                
                # Create match object
                match = Match(
                    center_x=max_loc[0] + w//2,
                    center_y=max_loc[1] + h//2,
                    confidence=max_val,
                    quality=quality
                )
                
                if self.debug:
                    self._save_debug_image(image, template, match)
                
                return match
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding template: {str(e)}")
            return None

    def find_all_matches(self, image, template, threshold=None, max_matches=10):
        """Find all occurrences of a template in an image."""
        if threshold is None:
            threshold = self.threshold
            
        try:
            # Convert images if needed
            if not isinstance(image, np.ndarray):
                image = np.array(image)
            if not isinstance(template, np.ndarray):
                template = np.array(template)
            
            # Convert to BGR if needed
            if len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            if len(template.shape) == 3 and template.shape[2] == 4:
                template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
            
            # Template matching
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            h, w = template.shape[:2]
            
            matches = []
            while len(matches) < max_matches:
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val < threshold:
                    break
                    
                # Get region for quality calculation
                region = image[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w]
                quality = self._calculate_quality(region, template)
                
                # Create match object
                match = Match(
                    center_x=max_loc[0] + w//2,
                    center_y=max_loc[1] + h//2,
                    confidence=max_val,
                    quality=quality
                )
                matches.append(match)
                
                # Mask out this match
                cv2.rectangle(
                    result,
                    max_loc,
                    (max_loc[0] + w, max_loc[1] + h),
                    0,
                    -1
                )
            
            if self.debug and matches:
                self._save_debug_image(image, template, matches[0])
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error finding all matches: {str(e)}")
            return []

    def _calculate_quality(self, region, template):
        """Calculate various similarity metrics between region and template."""
        try:
            # Structural similarity (template matching)
            ssim = cv2.matchTemplate(region, template, cv2.TM_CCOEFF_NORMED)[0][0]
            
            # Edge similarity
            edge1 = cv2.Canny(region, 100, 200)
            edge2 = cv2.Canny(template, 100, 200)
            edge_sim = cv2.matchTemplate(edge1, edge2, cv2.TM_CCOEFF_NORMED)[0][0]
            
            # Histogram similarity
            hist1 = cv2.calcHist([region], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([template], [0], None, [256], [0, 256])
            hist_sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            return MatchQuality(
                structural_similarity=float(ssim),
                edge_similarity=float(edge_sim),
                histogram_similarity=float(hist_sim)
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating quality metrics: {str(e)}")
            return MatchQuality(0.0, 0.0, 0.0)

    def _save_debug_image(self, image, template, match):
        """Save debug visualization of the match."""
        try:
            # Create debug image
            debug_img = image.copy()
            h, w = template.shape[:2]
            
            # Draw rectangle around match
            top_left = (match.center_x - w//2, match.center_y - h//2)
            bottom_right = (match.center_x + w//2, match.center_y + h//2)
            cv2.rectangle(debug_img, top_left, bottom_right, (0, 255, 0), 2)
            
            # Add confidence text
            text = f"Conf: {match.confidence:.2f}"
            cv2.putText(
                debug_img,
                text,
                (top_left[0], top_left[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )
            
            # Save image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = self.debug_dir / f'match_{timestamp}.png'
            cv2.imwrite(str(path), debug_img)
            
        except Exception as e:
            self.logger.error(f"Error saving debug image: {str(e)}") 