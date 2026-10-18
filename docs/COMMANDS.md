# Commands

Talk to the robot. Everything below works in the dashboard's chat box
(**Talk to the robot**). Portuguese and English both work.

## Chat commands

| You say | The robot does |
|---|---|
| `caminhe` · `walk` | Walks — in the live dream simulation |
| `levanta` · `stand` | Stands up in the dream |
| `cai` · `fall` | Falls over in the dream |
| `vira` · `flip` | Flips upside down in the dream |
| `sonha` · `dream` | Dreams again — fresh dream data |
| `acende` · lights on | Turns its real LED matrix **on** |
| `apaga` · lights off | Turns its real LED matrix **off** |
| `fala` · `speak` | Says what it knows about itself (its voice card updates) |
| `estado` · `status` | Reports its dream cycles and probe accuracy |
| `ajuda` · `help` | Lists these commands |

## Teach it a pose (on the board)

When the robot misreads a body pose, teach it the right answer —
it retrains itself on the device:

```bash
cd ~/walkersense
~/et-venv/bin/python teach.py add fallen 0.70 0.05 0.70 0 0 0   # label + 6 sensor values
~/et-venv/bin/python teach.py retrain                            # ~30 s, verified before swapping
```

The new model only goes live if the fixed probes still pass —
teaching can never make it worse.

## Teach it by camera

```bash
~/et-venv/bin/python vision_capture.py --label center --count 25  # photos of the object, per position
~/et-venv/bin/python vision_train.py                              # trains + exports the vision model
~/et-venv/bin/python vision.py                                    # live: watches and reports the zone
```

## The dashboard, briefly

- `/` — the interface (eyes, dream, beliefs, dreaming, mirror, chat,
  timeline)
- `/about` — the 5-slide presentation
- `/state.json` — everything the interface knows, as data
- `/command` — the chat endpoint (POST JSON: `{"text": "caminhe"}`)
