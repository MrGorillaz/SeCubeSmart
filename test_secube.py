import modules.secubeDriver as driver

cube = driver.secubeDriver(debug=True,port='/dev/ttyAMA5')
cube.get_version()

cube.get_status()
#cube.set_led_level(60)
cube.set_led_level(30)
cube