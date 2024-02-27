for sd in {1..20}
do
    python generate_maze.py \
    --rows 30 \
    --columns 30 \
    --visual \
    --seed $sd
done