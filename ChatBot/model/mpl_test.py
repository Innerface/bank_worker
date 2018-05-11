from pylab import *
import matplotlib.pyplot as plt
import matplotlib

zhfont1 = matplotlib.font_manager.FontProperties(fname='/Users/ruofanwu/Downloads/STHeiti Light.ttc')

t = arange(-5 * pi, 5 * pi, 0.01)
y = sin(t) / t
plt.plot(t, y)
plt.title('这里写的是中文')
plt.xlabel('X坐标')
plt.ylabel('Y坐标')
plt.show()