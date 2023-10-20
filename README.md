# iotaa-mpas

An iotaa workflow for MPAS

For example:

```
iotaa mpas ics ./runs 2023-10-19T12
```

For a graph
```
iotaa --graph mpas ics ./runs 2023-10-19T12 | dot -Tpng -og.png && qiv -t g.png
```
