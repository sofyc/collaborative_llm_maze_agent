for sd in {1..10}
do
    python generate_maze.py \
    --rows 10 \
    --columns 10 \
    --seed $sd
done