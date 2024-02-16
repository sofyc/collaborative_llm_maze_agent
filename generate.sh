for sd in {1..10}
do
    python generate_maze.py \
    --rows 20 \
    --columns 20 \
    --visual \
    --seed $sd
done