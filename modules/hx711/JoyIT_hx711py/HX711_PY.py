
import lgpio
import time

class HX711:
    def __init__(self, dout, pd_sck, gain=128):
        """
        Initialize the HX711 device.
        :param dout: Serial Data Output pin
        :param pd_sck: Power Down and Serial Clock Input pin
        :param gain: Amplifier gain (128, 64, or 32)
        """
        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1
        self.dout = dout
        self.pd_sck = pd_sck

        # Open GPIO chip
        self.h = lgpio.gpiochip_open(0)

        # Claim GPIO pins
        lgpio.gpio_claim_input(self.h, dout)
        lgpio.gpio_claim_output(self.h, pd_sck)

        # Power up the HX711 and set the gain
        self.power_up()
        self.set_gain(gain)

    def set_gain(self, gain=128):
        """
        Set the gain for the HX711 amplifier.
        :param gain: Amplifier gain (128, 64, or 32)
        """
        if gain == 128:
            self.GAIN = 3
        elif gain == 64:
            self.GAIN = 2
        elif gain == 32:
            self.GAIN = 1
        else:
            raise ValueError("Invalid gain value. Choose 128, 64, or 32.")

        lgpio.gpio_write(self.h, self.pd_sck, 0)  # Ensure SCK is LOW
        self.read()  # Perform a dummy read to set the gain

    def read(self):
        """
        Read a single data sample from the HX711.
        :return: 24-bit signed integer
        """
        # Wait until HX711 is ready
        while lgpio.gpio_read(self.h, self.dout):  # Check if DOUT is HIGH
            pass

        count = 0
        for _ in range(24):
            lgpio.gpio_write(self.h, self.pd_sck, 1)
            count = (count << 1) | lgpio.gpio_read(self.h, self.dout)
            lgpio.gpio_write(self.h, self.pd_sck, 0)

        # Complete the reading cycle
        lgpio.gpio_write(self.h, self.pd_sck, 1)
        count ^= 0x800000  # Convert from 2's complement
        lgpio.gpio_write(self.h, self.pd_sck, 0)

        # Set gain for the next reading
        for _ in range(self.GAIN):
            lgpio.gpio_write(self.h, self.pd_sck, 1)
            lgpio.gpio_write(self.h, self.pd_sck, 0)

        return count

    def read_average(self, times=16):
        """
        Compute the average of multiple readings.
        :param times: Number of samples
        :return: Average reading
        """
        return sum(self.read() for _ in range(times)) / times

    def get_grams(self, times=16):
        """
        Convert readings to grams.
        :param times: Number of samples for averaging
        :return: Weight in grams
        """
        value = self.read_average(times) - self.OFFSET
        return value / self.SCALE

    def tare(self, times=16):
        """
        Calibrate the HX711 by setting the current weight as zero.
        :param times: Number of samples for averaging
        """
        self.OFFSET = self.read_average(times)

    def set_scale(self, scale):
        """Set the scaling factor."""
        self.SCALE = scale

    def set_offset(self, offset):
        """Set the offset."""
        self.OFFSET = offset

    def power_down(self):
        """Power down the HX711."""
        lgpio.gpio_write(self.h, self.pd_sck, 0)
        time.sleep(0.0001)
        lgpio.gpio_write(self.h, self.pd_sck, 1)

    def power_up(self):
        """Power up the HX711."""
        lgpio.gpio_write(self.h, self.pd_sck, 0)

    def cleanup(self):
        """Release GPIO resources."""
        try:
            lgpio.gpiochip_close(self.h)
            print("HX711 GPIO resources released.")
        except Exception as e:
            print(f"Error during HX711 cleanup: {e}")

