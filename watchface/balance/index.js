const H_ROW = 169 // must match H_row computed by scripts/generate_assets.py
const SPLIT_Y = 240 // screen vertical center; hour/minute rows are equal height

const hourFontArray = []
const minuteFontArray = []
for (let i = 0; i <= 9; i++) {
  hourFontArray.push(`hour_${i}.png`)
  minuteFontArray.push(`minute_${i}.png`)
}

const HAND_POS_X = 231 // must match render_second_hand() output in scripts/generate_assets.py
const HAND_POS_Y = 43

let hourWidget, minuteWidget, secondHandWidget, timeSensor

function paint(hour, minute) {
  hourWidget.setProperty(hmUI.prop.TEXT, String(hour).padStart(2, '0'))
  minuteWidget.setProperty(hmUI.prop.TEXT, String(minute).padStart(2, '0'))
}

function paintSecondHand(second) {
  secondHandWidget.setProperty(hmUI.prop.MORE, { angle: second * 6 })
}

WatchFace({
  onInit() {},

  build() {
    hmUI.createWidget(hmUI.widget.IMG, { x: 0, y: 0, w: 480, h: 480, src: 'bg.png' })

    // drawn before (i.e. behind) the digit widgets, so it only peeks
    // through the gaps around the numbers instead of competing with them.
    secondHandWidget = hmUI.createWidget(hmUI.widget.IMG, {
      x: 0,
      y: 0,
      w: 480,
      h: 480,
      pos_x: HAND_POS_X,
      pos_y: HAND_POS_Y,
      center_x: 240,
      center_y: 240,
      src: 'second_hand.png',
      angle: 0,
    })

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
      paintSecondHand(timeSensor.second)

      timeSensor.addEventListener(timeSensor.event.MINUTEEND, function () {
        paint(timeSensor.hour, timeSensor.minute)
      })

      timer.createTimer(0, 1000, function () {
        paintSecondHand(timeSensor.second)
      })

      hmUI.createWidget(hmUI.widget.WIDGET_DELEGATE, {
        resume_call: function () {
          paint(timeSensor.hour, timeSensor.minute)
          paintSecondHand(timeSensor.second)
        },
      })
    } catch (e) {
      console.log('time sensor error: ' + e)
    }
  },

  onDestroy() {},
})
