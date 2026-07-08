const H_ROW = 169 // must match H_row computed by scripts/generate_assets.py
const SPLIT_Y = 240 // screen vertical center; hour/minute rows are equal height

const hourFontArray = []
const minuteFontArray = []
for (let i = 0; i <= 9; i++) {
  hourFontArray.push(`hour_${i}.png`)
  minuteFontArray.push(`minute_${i}.png`)
}

let hourWidget, minuteWidget, timeSensor

function paint(hour, minute) {
  hourWidget.setProperty(hmUI.prop.TEXT, String(hour).padStart(2, '0'))
  minuteWidget.setProperty(hmUI.prop.TEXT, String(minute).padStart(2, '0'))
}

WatchFace({
  onInit() {},

  build() {
    hmUI.createWidget(hmUI.widget.IMG, { x: 0, y: 0, w: 480, h: 480, src: 'bg.png' })

    hourWidget = hmUI.createWidget(hmUI.widget.TEXT_IMG, {
      x: 0,
      y: SPLIT_Y - H_ROW,
      w: 480,
      h: H_ROW,
      align_h: hmUI.align.CENTER_H,
      font_array: hourFontArray,
      h_space: 6,
      text: '10',
    })

    minuteWidget = hmUI.createWidget(hmUI.widget.TEXT_IMG, {
      x: 0,
      y: SPLIT_Y,
      w: 480,
      h: H_ROW,
      align_h: hmUI.align.CENTER_H,
      font_array: minuteFontArray,
      h_space: 6,
      text: '09',
    })

    try {
      if (!timeSensor) timeSensor = hmSensor.createSensor(hmSensor.id.TIME)
      paint(timeSensor.hour, timeSensor.minute)

      timeSensor.addEventListener(timeSensor.event.MINUTEEND, function () {
        paint(timeSensor.hour, timeSensor.minute)
      })

      hmUI.createWidget(hmUI.widget.WIDGET_DELEGATE, {
        resume_call: function () {
          paint(timeSensor.hour, timeSensor.minute)
        },
      })
    } catch (e) {
      console.log('time sensor error: ' + e)
    }
  },

  onDestroy() {},
})
