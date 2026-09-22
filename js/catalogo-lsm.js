/* Generado desde data/catalogo-lsm.json — no editar a mano */
window.LSM_CATALOG = {
  "version": "1.5.1",
  "idioma": "LSM",
  "nombre": "Alfabeto dactilológico mexicano",
  "modelo": {
    "archivo": "model2.glb",
    "descripcion": "Modelo oficial para la realización de las señas LSM. Rig Mixamo articulado (model2.glb); se anima la mano derecha para el alfabeto dactilológico.",
    "escala": [
      1,
      1,
      1
    ]
  },
  "rig": {
    "ejeCurl": "x",
    "curlSign": -1,
    "thumbCurlSign": 1,
    "transitionMs": 2000,
    "wristBone": "Right_Wrist",
    "cameraKnuckle": "Right_Middle_1",
    "framePerson": true,
    "cameraTarget": "0m 1.55m 0.04m",
    "cameraOrbit": "0deg 82deg 4.8m",
    "fieldOfView": "30deg",
    "cameraOffsetX": 0,
    "cameraOffsetY": 0.04,
    "cameraOffsetZ": 0.04,
    "restCorrections": [
      {
        "hueso": "Right_UpperArm",
        "rotaciones": [
          [
            "z",
            -80
          ],
          [
            "x",
            40
          ]
        ]
      },
      {
        "hueso": "Right_Forearm",
        "rotaciones": [
          [
            "x",
            -60
          ]
        ]
      },
      {
        "hueso": "Right_Wrist",
        "rotaciones": [
          [
            "x",
            -80
          ],
          [
            "z",
            -30
          ]
        ]
      },
      {
        "hueso": "Left_UpperArm",
        "rotaciones": [
          [
            "z",
            -40
          ],
          [
            "x",
            80
          ]
        ]
      }
    ],
    "jointOrder": {
      "thumb": [
        "trapez",
        [
          "meta",
          "prox"
        ],
        "dist"
      ],
      "dedo": [
        "prox",
        "midd",
        "dist"
      ]
    },
    "curlMaxGrados": {
      "prox": 72,
      "midd": 90,
      "dist": 68
    },
    "thumbCurlMaxGrados": {
      "trapez": 24,
      "meta": 34,
      "prox": 48,
      "dist": 42
    },
    "huesos": {
      "thumb": [
        "Right_Thumb_1",
        "Right_Thumb_2",
        "Right_Thumb_3"
      ],
      "index": [
        "Right_Index_1",
        "Right_Index_2",
        "Right_Index_3"
      ],
      "middle": [
        "Right_Middle_1",
        "Right_Middle_2",
        "Right_Middle_3"
      ],
      "ring": [
        "Right_Ring_1",
        "Right_Ring_2",
        "Right_Ring_3"
      ],
      "pinky": [
        "Right_Little_1",
        "Right_Little_2",
        "Right_Little_3"
      ]
    }
  },
  "senas": [
    {
      "letra": "○",
      "nombre": "Neutral",
      "descripcion": "Mano en reposo, sin modificar (pose original del modelo).",
      "animacion": null,
      "aliases": [
        "neutral",
        "reposo",
        "rest",
        "idle"
      ],
      "pose": null,
      "neutral": true
    },
    {
      "letra": "A",
      "nombre": "A",
      "descripcion": "Puño cerrado con los cuatro dedos recogidos y juntos; el pulgar se queda de pie al costado del índice, sin tumbarse por delante del puño (eso es la S) ni meterse entre índice y medio (eso es la T).",
      "animacion": "Letra_A",
      "aliases": [
        "A",
        "letra_a",
        "LSM_A"
      ],
      "pose": {
        "thumb": {
          "curl": 0.02
        },
        "index": {
          "curl": 1.0
        },
        "middle": {
          "curl": 1.0
        },
        "ring": {
          "curl": 1.0
        },
        "pinky": {
          "curl": 1.0
        },
        "muneca": {
          "x": -18,
          "y": 12,
          "z": 8
        },
        "extra": {
          "Right_UpperArm": {
            "z": -18
          },
          "Right_Index_1": {
            "z": 16
          },
          "Right_Index_2": {
            "z": 28
          },
          "Right_Index_3": {
            "z": 22
          },
          "Right_Middle_1": {
            "z": 16
          },
          "Right_Middle_2": {
            "z": 28
          },
          "Right_Middle_3": {
            "z": 22
          },
          "Right_Ring_1": {
            "z": 16
          },
          "Right_Ring_2": {
            "z": 28
          },
          "Right_Ring_3": {
            "z": 22
          },
          "Right_Little_1": {
            "z": 16
          },
          "Right_Little_2": {
            "z": 28
          },
          "Right_Little_3": {
            "z": 22
          },
          "Right_Thumb_1": {
            "x": 82,
            "y": -55,
            "z": 4
          },
          "Right_Thumb_2": {
            "x": -10
          },
          "Right_Thumb_3": {
            "x": -4
          }
        }
      }
    },
    {
      "letra": "B",
      "nombre": "B",
      "descripcion": "Palma al frente, cuatro dedos extendidos con un poco de espacio; pulgar pegado a la palma apuntando hacia arriba.",
      "animacion": "Letra_B",
      "aliases": [
        "B",
        "letra_b",
        "LSM_B"
      ],
      "pose": {
        "thumb": {
          "curl": 0.74,
          "aside": -0.5
        },
        "index": {
          "curl": 0.0,
          "spread": -4
        },
        "middle": {
          "curl": 0.0,
          "spread": 3
        },
        "ring": {
          "curl": 0.0,
          "spread": 4
        },
        "pinky": {
          "curl": 0.0,
          "spread": 6
        },
        "extra": {
          "Right_Thumb_1": {
            "y": -60
          }
        }
      }
    },
    {
      "letra": "C",
      "nombre": "C",
      "descripcion": "Mano de perfil delante del pecho, palma hacia el costado: los cuatro dedos juntos forman el arco de arriba y el pulgar opuesto lo cierra por abajo, dejando un hueco abierto con la forma de la letra C.",
      "animacion": "Letra_C",
      "aliases": [
        "C",
        "letra_c",
        "LSM_C"
      ],
      "pose": {
        "thumb": {
          "curl": 0.42,
          "aside": 0.8
        },
        "index": {
          "curl": 0.26,
          "spread": 4
        },
        "middle": {
          "curl": 0.26,
          "spread": 1
        },
        "ring": {
          "curl": 0.26,
          "spread": -1
        },
        "pinky": {
          "curl": 0.26,
          "spread": -4
        },
        "muneca": {
          "y": 90
        },
        "extra": {
          "Right_Index_1": {
            "x": 20
          },
          "Right_Middle_1": {
            "x": 20
          },
          "Right_Ring_1": {
            "x": 20
          },
          "Right_Little_1": {
            "x": 20
          },
          "Right_Index_2": {
            "x": 34
          },
          "Right_Middle_2": {
            "x": 34
          },
          "Right_Ring_2": {
            "x": 34
          },
          "Right_Little_2": {
            "x": 34
          },
          "Right_Index_3": {
            "x": 12
          },
          "Right_Middle_3": {
            "x": 12
          },
          "Right_Ring_3": {
            "x": 12
          },
          "Right_Little_3": {
            "x": 12
          },
          "Right_Thumb_1": {
            "y": 34,
            "z": 8
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      }
    },
    {
      "letra": "D",
      "nombre": "D",
      "descripcion": "Índice arriba; pulgar y dedo medio se juntan formando un círculo; anular y meñique cerrados.",
      "animacion": "Letra_D",
      "aliases": [
        "D",
        "letra_d",
        "LSM_D"
      ],
      "pose": {
        "thumb": {
          "curl": 0.58,
          "aside": 0.4
        },
        "index": {
          "curl": 0.0
        },
        "middle": {
          "curl": 0.61
        },
        "ring": {
          "curl": 0.92
        },
        "pinky": {
          "curl": 0.92
        },
        "extra": {
          "Right_Thumb_1": {
            "z": 41,
            "y": -6
          },
          "Right_Thumb_2": {
            "x": -41
          },
          "Right_Thumb_3": {
            "x": -10
          },
          "Right_Middle_2": {
            "x": 10
          },
          "Right_Middle_3": {
            "x": 16
          }
        }
      }
    },
    {
      "letra": "E",
      "nombre": "E",
      "descripcion": "Puño compacto con la palma al frente: los cuatro dedos, juntos y doblados por igual, se enrollan hasta que las yemas quedan justo debajo de los nudillos; el pulgar cruza la palma tumbado y en horizontal, justo por debajo de las yemas, que se apoyan encima de él.",
      "animacion": "Letra_E",
      "aliases": [
        "E",
        "letra_e",
        "LSM_E"
      ],
      "pose": {
        "thumb": {
          "curl": 0.59,
          "aside": -0.96
        },
        "index": {
          "curl": 0.92,
          "spread": -12
        },
        "middle": {
          "curl": 0.92,
          "spread": -4
        },
        "ring": {
          "curl": 0.92,
          "spread": 4
        },
        "pinky": {
          "curl": 0.92,
          "spread": 12
        },
        "extra": {
          "Right_Thumb_1": {
            "x": 60,
            "y": -35,
            "z": 78
          },
          "Right_Thumb_2": {
            "x": 24
          },
          "Right_Thumb_3": {
            "x": -11
          },
          "Right_Index_1": {
            "x": 4.8
          },
          "Right_Index_2": {
            "x": 6.6
          },
          "Right_Index_3": {
            "x": 20.2
          },
          "Right_Middle_2": {
            "x": 4.8
          },
          "Right_Middle_3": {
            "x": 31
          },
          "Right_Ring_1": {
            "x": -8.5
          },
          "Right_Ring_2": {
            "x": 9.7
          },
          "Right_Ring_3": {
            "x": 47.1
          },
          "Right_Little_1": {
            "x": -6.5
          },
          "Right_Little_3": {
            "x": 22.8
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      }
    },
    {
      "letra": "F",
      "nombre": "F",
      "descripcion": "Palma al frente: pulgar vertical; yemas de pulgar e índice se tocan formando círculo, sin cruzarse; medio, anular y meñique extendidos.",
      "animacion": "Letra_F",
      "aliases": [
        "F",
        "letra_f",
        "LSM_F"
      ],
      "pose": {
        "thumb": {
          "curl": 0.2
        },
        "index": {
          "curl": 0.5,
          "spread": 8
        },
        "middle": {
          "curl": 0.0,
          "spread": 3
        },
        "ring": {
          "curl": 0.0,
          "spread": 4
        },
        "pinky": {
          "curl": 0.0,
          "spread": 6
        },
        "extra": {
          "Right_Thumb_1": {
            "z": 30
          }
        }
      }
    },
    {
      "letra": "G",
      "nombre": "G",
      "descripcion": "Índice y pulgar extendidos en paralelo (hacia el lado).",
      "animacion": "Letra_G",
      "aliases": [
        "G",
        "letra_g",
        "LSM_G"
      ],
      "pose": {
        "thumb": {
          "curl": 0.05,
          "aside": 0.6
        },
        "index": {
          "curl": 0.05
        },
        "middle": {
          "curl": 0.95
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "muneca": {
          "z": 90
        }
      }
    },
    {
      "letra": "H",
      "nombre": "H",
      "descripcion": "Índice y medio extendidos juntos; resto cerrado.",
      "animacion": "Letra_H",
      "aliases": [
        "H",
        "letra_h",
        "LSM_H"
      ],
      "pose": {
        "thumb": {
          "curl": 0.55
        },
        "index": {
          "curl": 0.05
        },
        "middle": {
          "curl": 0.05
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "muneca": {
          "z": 90
        }
      }
    },
    {
      "letra": "I",
      "nombre": "I",
      "descripcion": "Meñique arriba; resto de dedos cerrados.",
      "animacion": "Letra_I",
      "aliases": [
        "I",
        "letra_i",
        "LSM_I"
      ],
      "pose": {
        "thumb": {
          "curl": 0.6
        },
        "index": {
          "curl": 0.95
        },
        "middle": {
          "curl": 0.95
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.0
        }
      }
    },
    {
      "letra": "J",
      "nombre": "J",
      "descripcion": "Igual que la I (meñique arriba) y la muñeca traza una media luna: baja, curva por abajo y engancha hacia la izquierda dibujando la J.",
      "animacion": "Letra_J",
      "aliases": [
        "J",
        "letra_j",
        "LSM_J"
      ],
      "pose": {
        "thumb": {
          "curl": 0.6
        },
        "index": {
          "curl": 0.95
        },
        "middle": {
          "curl": 0.95
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.05
        },
        "muneca": {
          "y": -12
        }
      },
      "ciclo": {
        "holdStartMs": 600,
        "durationMs": 1500,
        "holdEndMs": 450,
        "resetMs": 550,
        "loop": true,
        "keyframes": [
          {
            "t": 0.0,
            "muneca": {
              "x": 0,
              "y": -12,
              "z": 0
            },
            "extra": {
              "Right_Forearm": {
                "x": 0
              }
            }
          },
          {
            "t": 0.15,
            "muneca": {
              "x": 3,
              "y": -12,
              "z": -14
            },
            "extra": {
              "Right_Forearm": {
                "x": 12
              }
            }
          },
          {
            "t": 0.3,
            "muneca": {
              "x": 5,
              "y": -12,
              "z": -16
            },
            "extra": {
              "Right_Forearm": {
                "x": 27
              }
            }
          },
          {
            "t": 0.45,
            "muneca": {
              "x": 6,
              "y": -12,
              "z": -4
            },
            "extra": {
              "Right_Forearm": {
                "x": 38
              }
            }
          },
          {
            "t": 0.6,
            "muneca": {
              "x": 5,
              "y": -13,
              "z": 20
            },
            "extra": {
              "Right_Forearm": {
                "x": 42
              }
            }
          },
          {
            "t": 0.75,
            "muneca": {
              "x": 3,
              "y": -14,
              "z": 46
            },
            "extra": {
              "Right_Forearm": {
                "x": 34
              }
            }
          },
          {
            "t": 0.88,
            "muneca": {
              "x": 1,
              "y": -15,
              "z": 68
            },
            "extra": {
              "Right_Forearm": {
                "x": 18
              }
            }
          },
          {
            "t": 1.0,
            "muneca": {
              "x": 0,
              "y": -16,
              "z": 84
            },
            "extra": {
              "Right_Forearm": {
                "x": 2
              }
            }
          }
        ]
      }
    },
    {
      "letra": "K",
      "nombre": "K",
      "descripcion": "Índice arriba, medio inclinado; pulgar entre ambos. La muñeca hace un vaivén: la mano se inclina hacia adelante y regresa hacia atrás, sin mover el brazo.",
      "animacion": "Letra_K",
      "aliases": [
        "K",
        "letra_k",
        "LSM_K"
      ],
      "pose": {
        "thumb": {
          "curl": 0.25,
          "aside": 0.2
        },
        "index": {
          "curl": 0.0
        },
        "middle": {
          "curl": 0.4
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "muneca": {
          "x": -18
        }
      },
      "ciclo": {
        "holdStartMs": 350,
        "durationMs": 1200,
        "holdEndMs": 300,
        "resetMs": 1200,
        "loop": true,
        "keyframes": [
          {
            "t": 0.0,
            "muneca": {
              "x": -18,
              "y": 0,
              "z": 0
            }
          },
          {
            "t": 0.5,
            "muneca": {
              "x": 6,
              "y": 0,
              "z": 0
            }
          },
          {
            "t": 1.0,
            "muneca": {
              "x": 30,
              "y": 0,
              "z": 0
            }
          }
        ]
      }
    },
    {
      "letra": "L",
      "nombre": "L",
      "descripcion": "Índice arriba y pulgar al lado formando L.",
      "animacion": "Letra_L",
      "aliases": [
        "L",
        "letra_l",
        "LSM_L"
      ],
      "pose": {
        "thumb": {
          "curl": 0.05,
          "aside": 0.55
        },
        "index": {
          "curl": 0.0
        },
        "middle": {
          "curl": 0.95
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        }
      }
    },
    {
      "letra": "M",
      "nombre": "M",
      "descripcion": "Índice, medio y anular cuelgan hacia abajo (como volando); la muñeca se inclina para que apunten al piso; el pulgar sujeta el meñique cerrado.",
      "animacion": "Letra_M",
      "aliases": [
        "M",
        "letra_m",
        "LSM_M"
      ],
      "pose": {
        "thumb": {
          "curl": 0.74,
          "aside": -0.5
        },
        "index": {
          "curl": 0.12,
          "spread": 16
        },
        "middle": {
          "curl": 0.12
        },
        "ring": {
          "curl": 0.12,
          "spread": -16
        },
        "pinky": {
          "curl": 0.95
        },
        "muneca": {
          "x": 150
        },
        "extra": {
          "Right_Thumb_1": {
            "y": -60,
            "x": -12
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      }
    },
    {
      "letra": "N",
      "nombre": "N",
      "descripcion": "Índice y medio cuelgan hacia abajo, juntos y apuntando al piso (la M con dos dedos); la muñeca se inclina para que caigan, y anular y meñique quedan cerrados con el pulgar encima.",
      "animacion": "Letra_N",
      "aliases": [
        "N",
        "letra_n",
        "LSM_N"
      ],
      "pose": {
        "thumb": {
          "curl": 0.74,
          "aside": -0.5
        },
        "index": {
          "curl": 0.12,
          "spread": 9
        },
        "middle": {
          "curl": 0.12,
          "spread": -3
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "muneca": {
          "x": 150
        },
        "extra": {
          "Right_Thumb_1": {
            "y": -60,
            "x": -12
          },
          "Right_Ring_1": {
            "x": 8
          },
          "Right_Ring_2": {
            "x": 24
          },
          "Right_Ring_3": {
            "x": 26
          },
          "Right_Little_1": {
            "x": 8
          },
          "Right_Little_2": {
            "x": 24
          },
          "Right_Little_3": {
            "x": 26
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      }
    },
    {
      "letra": "Ñ",
      "nombre": "Ñ",
      "descripcion": "Como la N —índice y medio colgando y el resto cerrado— y la mano se desliza de izquierda a derecha, sin cambiar de forma, para marcar la tilde.",
      "animacion": "Letra_Ñ",
      "aliases": [
        "Ñ",
        "letra_ñ",
        "LSM_Ñ",
        "ene"
      ],
      "pose": {
        "thumb": {
          "curl": 0.74,
          "aside": -0.5
        },
        "index": {
          "curl": 0.12,
          "spread": 9
        },
        "middle": {
          "curl": 0.12,
          "spread": -3
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "muneca": {
          "x": 150,
          "y": 12
        },
        "extra": {
          "Right_Thumb_1": {
            "y": -60,
            "x": -12
          },
          "Right_Ring_1": {
            "x": 8
          },
          "Right_Ring_2": {
            "x": 24
          },
          "Right_Ring_3": {
            "x": 26
          },
          "Right_Little_1": {
            "x": 8
          },
          "Right_Little_2": {
            "x": 24
          },
          "Right_Little_3": {
            "x": 26
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      },
      "ciclo": {
        "etiqueta": "la mano se desliza de izquierda a derecha",
        "holdStartMs": 500,
        "durationMs": 1300,
        "holdEndMs": 350,
        "resetMs": 900,
        "loop": true,
        "keyframes": [
          {
            "t": 0.0,
            "muneca": {
              "x": 150,
              "y": 12,
              "z": 0
            },
            "extra": {
              "Right_UpperArm": {
                "y": 22,
                "z": -18
              }
            }
          },
          {
            "t": 0.5,
            "muneca": {
              "x": 150,
              "y": 12,
              "z": 0
            },
            "extra": {
              "Right_UpperArm": {
                "y": 10,
                "z": -18
              }
            }
          },
          {
            "t": 1.0,
            "muneca": {
              "x": 150,
              "y": 12,
              "z": 0
            },
            "extra": {
              "Right_UpperArm": {
                "y": -2,
                "z": -18
              }
            }
          }
        ]
      }
    },
    {
      "letra": "O",
      "nombre": "O",
      "descripcion": "Mano de perfil delante del pecho, palma hacia el costado: los cuatro dedos, juntos y curvados por igual, bajan formando el arco de arriba y el pulgar sube a su encuentro hasta que las yemas se tocan, dejando un hueco redondo con la forma de la letra O.",
      "animacion": "Letra_O",
      "aliases": [
        "O",
        "letra_o",
        "LSM_O"
      ],
      "pose": {
        "thumb": {
          "curl": 0.35,
          "aside": -0.5
        },
        "index": {
          "curl": 0.625,
          "spread": 4
        },
        "middle": {
          "curl": 0.625,
          "spread": 1.3
        },
        "ring": {
          "curl": 0.625,
          "spread": -1.3
        },
        "pinky": {
          "curl": 0.625,
          "spread": -4
        },
        "muneca": {
          "y": 70
        },
        "extra": {
          "Right_Thumb_1": {
            "x": -15,
            "y": 10,
            "z": 15
          },
          "Right_Thumb_2": {
            "x": 25
          },
          "Right_Thumb_3": {
            "x": 35
          },
          "Right_Index_1": {
            "x": 14.1
          },
          "Right_Index_2": {
            "x": 2
          },
          "Right_Index_3": {
            "x": -16.2
          },
          "Right_Middle_1": {
            "x": 12
          },
          "Right_Middle_2": {
            "x": 2
          },
          "Right_Middle_3": {
            "x": -6
          },
          "Right_Ring_1": {
            "x": 7.1
          },
          "Right_Ring_2": {
            "x": 6.6
          },
          "Right_Ring_3": {
            "x": 10.9
          },
          "Right_Little_1": {
            "x": 14.6
          },
          "Right_Little_2": {
            "x": -3.9
          },
          "Right_Little_3": {
            "x": -13.5
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      }
    },
    {
      "letra": "P",
      "nombre": "P",
      "descripcion": "Índice estirado en diagonal hacia arriba y dedo medio tumbado desde el nudillo hasta quedar horizontal, formando escuadra; el pulgar se recoge en la base del medio y anular y meñique quedan cerrados. La muñeca gira para poner la mano de perfil y además se dobla, de modo que la escuadra queda inclinada como en una mano real.",
      "animacion": "Letra_P",
      "aliases": [
        "P",
        "letra_p",
        "LSM_P"
      ],
      "pose": {
        "thumb": {
          "curl": 0.85,
          "aside": -0.3
        },
        "index": {
          "curl": 0.0,
          "spread": 4
        },
        "middle": {
          "curl": 0.0,
          "spread": -4
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "muneca": {
          "y": 95
        },
        "extra": {
          "Right_Wrist": {
            "x": 24,
            "y": 10
          },
          "Right_Middle_1": {
            "x": 55
          },
          "Right_Thumb_1": {
            "y": -85
          },
          "Right_Thumb_2": {
            "x": 25
          },
          "Right_UpperArm": {
            "z": -30
          }
        }
      }
    },
    {
      "letra": "Q",
      "nombre": "Q",
      "descripcion": "Como la G pero con la mano vuelta hacia abajo: el índice baja en diagonal con la yema enganchada y el pulgar cuelga por dentro, dejando entre las dos yemas el hueco del pico; medio, anular y meñique quedan cerrados. Sin cambiar de forma, la mano dibuja en el aire un círculo pequeño en sentido de las manecillas del reloj: el redondel de la Q.",
      "animacion": "Letra_Q",
      "aliases": [
        "Q",
        "letra_q",
        "LSM_Q"
      ],
      "pose": {
        "thumb": {
          "curl": 0.3,
          "aside": 0.3
        },
        "index": {
          "curl": 0.0
        },
        "middle": {
          "curl": 0.95
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "muneca": {
          "x": 135,
          "z": 45
        },
        "extra": {
          "Right_Index_3": {
            "x": 45
          },
          "Right_Thumb_1": {
            "y": -40,
            "z": -20
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      },
      "ciclo": {
        "etiqueta": "la mano dibuja el redondel de la Q",
        "holdStartMs": 450,
        "durationMs": 1700,
        "holdEndMs": 350,
        "resetMs": 250,
        "ease": "linear",
        "loop": true,
        "keyframes": [
          {
            "t": 0.0,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": 0.11,
                "z": -18
              },
              "Right_Forearm": {
                "x": -8.86
              }
            }
          },
          {
            "t": 0.0833,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": 5.19,
                "z": -18
              },
              "Right_Forearm": {
                "x": -8.77
              }
            }
          },
          {
            "t": 0.1667,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": 8.89,
                "z": -18
              },
              "Right_Forearm": {
                "x": -6.32
              }
            }
          },
          {
            "t": 0.25,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": 10.2,
                "z": -18
              },
              "Right_Forearm": {
                "x": -2.18
              }
            }
          },
          {
            "t": 0.3333,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": 8.77,
                "z": -18
              },
              "Right_Forearm": {
                "x": 2.54
              }
            }
          },
          {
            "t": 0.4167,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": 5.0,
                "z": -18
              },
              "Right_Forearm": {
                "x": 6.59
              }
            }
          },
          {
            "t": 0.5,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": -0.11,
                "z": -18
              },
              "Right_Forearm": {
                "x": 8.86
              }
            }
          },
          {
            "t": 0.5833,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": -5.19,
                "z": -18
              },
              "Right_Forearm": {
                "x": 8.77
              }
            }
          },
          {
            "t": 0.6667,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": -8.89,
                "z": -18
              },
              "Right_Forearm": {
                "x": 6.32
              }
            }
          },
          {
            "t": 0.75,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": -10.2,
                "z": -18
              },
              "Right_Forearm": {
                "x": 2.18
              }
            }
          },
          {
            "t": 0.8333,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": -8.77,
                "z": -18
              },
              "Right_Forearm": {
                "x": -2.54
              }
            }
          },
          {
            "t": 0.9167,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": -5.0,
                "z": -18
              },
              "Right_Forearm": {
                "x": -6.59
              }
            }
          },
          {
            "t": 1.0,
            "muneca": {
              "x": 135,
              "y": 0,
              "z": 45
            },
            "extra": {
              "Right_UpperArm": {
                "x": 0.11,
                "z": -18
              },
              "Right_Forearm": {
                "x": -8.86
              }
            }
          }
        ]
      }
    },
    {
      "letra": "R",
      "nombre": "R",
      "descripcion": "Índice y medio estirados hacia arriba y cruzados: el índice se adelanta y monta por delante del medio, de modo que las dos yemas quedan cambiadas de lado y juntas arriba, dibujando la equis de la R. Anular y meñique se recogen en el puño con el pulgar tumbado encima.",
      "animacion": "Letra_R",
      "aliases": [
        "R",
        "letra_r",
        "LSM_R"
      ],
      "pose": {
        "thumb": {
          "curl": 0.35,
          "aside": -0.6
        },
        "index": {
          "curl": 0.0
        },
        "middle": {
          "curl": 0.0
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "extra": {
          "Right_UpperArm": {
            "z": -18
          },
          "Right_Index_1": {
            "x": 32,
            "z": 22
          },
          "Right_Index_2": {
            "x": -40,
            "z": -10
          },
          "Right_Middle_1": {
            "z": -26
          },
          "Right_Thumb_1": {
            "y": -30,
            "z": 40
          },
          "Right_Thumb_2": {
            "x": 60
          }
        }
      }
    },
    {
      "letra": "S",
      "nombre": "S",
      "descripcion": "Puño cerrado con el pulgar tumbado cruzando por delante de los dedos: se apoya sobre las falanges medias del índice y el medio y la yema queda apuntando hacia el anular. Es lo que la distingue de la A, donde el pulgar se queda de pie al costado del índice en vez de montar por delante del puño.",
      "animacion": "Letra_S",
      "aliases": [
        "S",
        "letra_s",
        "LSM_S"
      ],
      "pose": {
        "thumb": {
          "curl": 0.4
        },
        "index": {
          "curl": 0.9
        },
        "middle": {
          "curl": 0.9
        },
        "ring": {
          "curl": 0.9
        },
        "pinky": {
          "curl": 0.9
        },
        "extra": {
          "Right_UpperArm": {
            "z": -18
          },
          "Right_Index_1": {
            "x": 30
          },
          "Right_Middle_1": {
            "x": 30
          },
          "Right_Ring_1": {
            "x": 30
          },
          "Right_Little_1": {
            "x": 30
          },
          "Right_Thumb_1": {
            "x": 20,
            "y": -75
          },
          "Right_Thumb_2": {
            "x": 45,
            "y": -25
          }
        }
      }
    },
    {
      "letra": "T",
      "nombre": "T",
      "descripcion": "Puño cerrado; el pulgar se mete bajo el índice y la yema asoma entre índice y medio. Es lo que la distingue de la A, donde el pulgar queda de pie al costado del índice, y de la S, donde el pulgar va tumbado cruzando por delante de los dedos.",
      "animacion": "Letra_T",
      "aliases": [
        "T",
        "letra_t",
        "LSM_T"
      ],
      "pose": {
        "thumb": {
          "curl": 0.35
        },
        "index": {
          "curl": 0.9,
          "spread": -16
        },
        "middle": {
          "curl": 0.9,
          "spread": 16
        },
        "ring": {
          "curl": 0.9
        },
        "pinky": {
          "curl": 0.9
        },
        "extra": {
          "Right_Thumb_1": {
            "x": -55,
            "y": 30,
            "z": 56
          },
          "Right_Thumb_3": {
            "x": -5
          },
          "Right_Index_1": {
            "x": 30
          },
          "Right_Middle_1": {
            "x": 30
          },
          "Right_Ring_1": {
            "x": 30
          },
          "Right_Little_1": {
            "x": 30
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      }
    },
    {
      "letra": "U",
      "nombre": "U",
      "descripcion": "Índice y medio estirados hacia arriba y pegados en toda su longitud, sin cruzarse: es lo que la distingue de la V, donde esos dos dedos se abren, y de la R, donde se cruzan. Anular y meñique se recogen en el puño con el pulgar tumbado encima, apoyado sobre las falanges de esos dos.",
      "animacion": "Letra_U",
      "aliases": [
        "U",
        "letra_u",
        "LSM_U"
      ],
      "pose": {
        "thumb": {
          "curl": 0.35,
          "aside": -0.6
        },
        "index": {
          "curl": 0.0
        },
        "middle": {
          "curl": 0.0
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "extra": {
          "Right_Index_1": {
            "z": 8
          },
          "Right_Middle_1": {
            "z": -8
          },
          "Right_Thumb_1": {
            "y": -30,
            "z": 40
          },
          "Right_Thumb_2": {
            "x": 60
          }
        }
      }
    },
    {
      "letra": "V",
      "nombre": "V",
      "descripcion": "Índice y medio estirados hacia arriba y separados en una V estrecha (unos 30-35 grados, no el signo de victoria abierto). Anular y meñique se recogen en el puño con el pulgar tumbado encima, apoyado sobre las falanges de esos dos, sin montar en los dedos largos.",
      "animacion": "Letra_V",
      "aliases": [
        "V",
        "letra_v",
        "LSM_V"
      ],
      "pose": {
        "thumb": {
          "curl": 0.35,
          "aside": -0.6
        },
        "index": {
          "curl": 0.0,
          "spread": -10
        },
        "middle": {
          "curl": 0.0,
          "spread": 10
        },
        "ring": {
          "curl": 0.95
        },
        "pinky": {
          "curl": 0.95
        },
        "extra": {
          "Right_Thumb_1": {
            "y": -30,
            "z": 40
          },
          "Right_Thumb_2": {
            "x": 60
          }
        }
      }
    },
    {
      "letra": "W",
      "nombre": "W",
      "descripcion": "Índice, medio y anular estirados hacia arriba, con un hueco visible entre cada uno, como los tres palitos de la W (sin abrirlos en abanico). El meñique se recoge contra la palma y el pulgar queda tumbado encima, con la yema apoyada sobre el meñique.",
      "animacion": "Letra_W",
      "aliases": [
        "W",
        "letra_w",
        "LSM_W"
      ],
      "pose": {
        "thumb": {
          "curl": 0.35,
          "aside": -0.6
        },
        "index": {
          "curl": 0.0,
          "spread": -6
        },
        "middle": {
          "curl": 0.0
        },
        "ring": {
          "curl": 0.0,
          "spread": 12
        },
        "pinky": {
          "curl": 0.95
        },
        "extra": {
          "Right_Thumb_1": {
            "y": -30,
            "z": 50
          },
          "Right_Thumb_2": {
            "x": 60
          }
        }
      }
    },
    {
      "letra": "X",
      "nombre": "X",
      "descripcion": "Puño de pie delante del pecho, palma hacia el cuerpo: el índice sale del puño y se dobla en gancho apuntando a la izquierda; medio, anular y meñique van cerrados y el pulgar se recuesta al costado del medio, debajo del gancho. Sin cambiar de forma, la mano entera se jala en diagonal hacia arriba y a la derecha (la flecha de la lámina); el movimiento sale del antebrazo, no de un giro de muñeca.",
      "animacion": "Letra_X",
      "aliases": [
        "X",
        "letra_x",
        "LSM_X"
      ],
      "pose": {
        "thumb": {
          "curl": 0.25,
          "aside": 0.4
        },
        "index": {
          "curl": 0.0
        },
        "middle": {
          "curl": 1.0
        },
        "ring": {
          "curl": 1.0
        },
        "pinky": {
          "curl": 1.0
        },
        "muneca": {
          "x": 20,
          "y": 12,
          "z": -90
        },
        "extra": {
          "Right_Index_1": {
            "x": 18
          },
          "Right_Index_2": {
            "x": 78
          },
          "Right_Index_3": {
            "x": 58
          },
          "Right_Thumb_1": {
            "y": -12
          },
          "Right_UpperArm": {
            "z": -18
          }
        }
      },
      "ciclo": {
        "etiqueta": "la mano se jala en diagonal hacia arriba y a la derecha",
        "holdStartMs": 450,
        "durationMs": 850,
        "holdEndMs": 400,
        "resetMs": 750,
        "loop": true,
        "keyframes": [
          {
            "t": 0.0,
            "muneca": {
              "x": 20,
              "y": 12,
              "z": -90
            },
            "extra": {
              "Right_UpperArm": {
                "z": -18
              },
              "Right_Forearm": {
                "x": 0,
                "z": 0
              }
            }
          },
          {
            "t": 1.0,
            "muneca": {
              "x": 20,
              "y": 12,
              "z": -90
            },
            "extra": {
              "Right_UpperArm": {
                "z": -18
              },
              "Right_Forearm": {
                "x": 12,
                "z": -12
              }
            }
          }
        ]
      }
    },
    {
      "letra": "Y",
      "nombre": "Y",
      "descripcion": "Pulgar estirado hacia arriba y meñique hacia un lado, formando la Y; índice, medio y anular se cierran contra la palma. La muñeca gira en el plano de la palma para que se lean los dos palitos, con el antebrazo en diagonal y la muñeca alineada (sin quebrarla).",
      "animacion": "Letra_Y",
      "aliases": [
        "Y",
        "letra_y",
        "LSM_Y"
      ],
      "pose": {
        "thumb": {
          "curl": 0.0,
          "aside": 0.85
        },
        "index": {
          "curl": 0.98
        },
        "middle": {
          "curl": 0.98
        },
        "ring": {
          "curl": 0.98
        },
        "pinky": {
          "curl": 0.0,
          "spread": 22
        },
        "extra": {
          "Right_UpperArm": {
            "z": -18
          },
          "Right_Forearm": {
            "x": 8,
            "z": 6
          },
          "Right_Thumb_1": {
            "z": 16
          }
        },
        "muneca": {
          "x": 6,
          "z": 52
        }
      }
    },
    {
      "letra": "Z",
      "nombre": "Z",
      "descripcion": "Índice estirado hacia arriba y el resto en puño, palma al frente: el dedo es el lápiz. Sin cambiar de forma, la mano entera —muñeca y antebrazo juntos— dibuja una Z mayúscula en el aire: trazo horizontal a la derecha, diagonal abajo-izquierda y otra vez horizontal a la derecha.",
      "animacion": "Letra_Z",
      "aliases": [
        "Z",
        "letra_z",
        "LSM_Z"
      ],
      "pose": {
        "thumb": {
          "curl": 0.55,
          "aside": 0.12
        },
        "index": {
          "curl": 0.0
        },
        "middle": {
          "curl": 0.98
        },
        "ring": {
          "curl": 0.98
        },
        "pinky": {
          "curl": 0.98
        },
        "extra": {
          "Right_UpperArm": {
            "z": -18
          },
          "Right_Forearm": {
            "x": -21.58,
            "z": 12.87
          }
        }
      },
      "ciclo": {
        "etiqueta": "el índice dibuja una Z en el aire",
        "holdStartMs": 500,
        "durationMs": 1600,
        "holdEndMs": 400,
        "resetMs": 700,
        "ease": "linear",
        "loop": true,
        "keyframes": [
          {
            "t": 0.0,
            "extra": {
              "Right_UpperArm": {
                "z": -18
              },
              "Right_Forearm": {
                "x": -21.58,
                "z": 12.87
              }
            }
          },
          {
            "t": 0.293,
            "extra": {
              "Right_UpperArm": {
                "z": -18
              },
              "Right_Forearm": {
                "x": -17.38,
                "z": -14.0
              }
            }
          },
          {
            "t": 0.707,
            "extra": {
              "Right_UpperArm": {
                "z": -18
              },
              "Right_Forearm": {
                "x": 17.38,
                "z": 14.0
              }
            }
          },
          {
            "t": 1.0,
            "extra": {
              "Right_UpperArm": {
                "z": -18
              },
              "Right_Forearm": {
                "x": 21.58,
                "z": -12.87
              }
            }
          }
        ]
      }
    }
  ]
};
