import modules.secubeDriver as driver

cube = driver.secubeDriver(port='/dev/ttyAMA5')
cube.get_version()

cube.get_status()
cube.__read_config(version=1)
#cube.set_led_level(60)
cube.set_led_level(10)
cube