

from PIL import Image, ImageEnhance
import numpy as np
import cv2

def adjust_blue_saturation(image_path, output_path, saturation_factor):
    """
    Adjust the saturation of blue areas in an image.

    :param image_path: Path to the input image.
    :param output_path: Path to save the output image.
    :param saturation_factor: A float where 1 means no change, less than 1 means less saturation,
                              and greater than 1 means more saturation.
    """

    # Open an image file
    with Image.open(image_path) as img:
        # Convert the image to RGB mode if it's not already
        img = img.convert('RGB')
        
        # Convert the image to a numpy array
        img_array = np.array(img)
        
        # Convert the image to HSV color space
        hsv_img = Image.fromarray(img_array, 'RGB').convert('HSV')
        hsv_array = np.array(hsv_img)

        # Define the blue color range in HSV
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([140, 255, 255])
        
        # Create a mask for blue areas
        mask = cv2.inRange(hsv_array, lower_blue, upper_blue)
        
        # Apply the mask to the HSV image to adjust saturation
        hsv_array[mask > 0, 1] = hsv_array[mask > 0, 1] * saturation_factor
        hsv_array[hsv_array > 255] = 255  # Ensure saturation does not exceed 255
        
        # Convert the adjusted HSV image back to RGB
        adjusted_img = Image.fromarray(hsv_array, 'HSV').convert('RGB')
        
        # Save the adjusted image
        adjusted_img.save(output_path)


if __name__ == "__main__":

    input_path = 'F:/微信图片_20250322154158.jpg'
    output_path = 'F:/微信图片_20250322154158_output.jpg'
    saturation_factor = 0.1
    adjust_blue_saturation(input_path, output_path, saturation_factor)  # Increase saturation by 50%