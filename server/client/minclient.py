#!/usr/bin/env python
import zlib, base64
exec(zlib.decompress(base64.b64decode('eJy1WVtz27iSfuevYLQPJI8ZypmTk53jMnLKF8lRpNiKZTr2alQq3iTQpkiGoCzJUzO/fbtxoUhJmUzV1r5IQKPR6G583WiA//WmvWRF24/TdpS+6PmmpFmqsYLcFctIYyW5zlL475Nyk8P/gLCy0NgT8TdlxDSWkiQC9iHprIMoL2Oc+0K6XsKA+ZEkMSs19omEcQD/DyTLkXtFbkadoshAUELiFEYiEodavMizotRZFjxHpeZ+J6LlzKPSC8MiTmeZ5i4VVbHNFOGsO+1dd+40905RRjcX/eno7rZz9qUSvvTzIgsixjR3Q7Y9Z9gbdjT3ukHi2qqJG7CWEvhzWBlGRaG556qXLcEEl/cW3prFr2B7j3e9Yv6isVfejtZRsCw9P4mUzAxEeiQTQ8AXYDv3SqqxETZZ6YHgS2ym3gKEXmETfRrGhRKSJ145y4qFxjKi2g6sV0ZA+rolLbxg+hKByztbWhElkccqfRhdlnGisTURLSfI8o0aLGPU4Jbgv8OSKMrVyBPDXX8m+O+Ey0UOZi1EL8m8kFUSaBF5YZzONZaTquPc8ZbGzmq0AWygxvwa5SJLw5jjSylbFksE1WciWuA4nBOr7jLlBMntg5kf3mvshoiW4394H6VBFoJN32q0MOI0pXHhBZHP5Yak6jjoO6+cRuugUoaB2+YE/pxV4eVTCU45CgDOPUAcuyeyiZheMtiNsticaPqsyBb6qASIz3s3upyl+lrEQ0uxxdkewxQ3loFvplPSeucctzRKjH8dO+/+9W/nwwfnl39+MDSXvPvv4181RgyHZqw0tB604tDQXomBeEoNLSBG9OIlhjYiRrCAoUtiPMcJEK6IAdanbBYVhuYRAyyI5zAjI0bCDO0rMcJsBf0OMWbg/shbGNoa2kGSscjQbqGJADa0Z5CsGBbQlgxnRNliWppPWKHlxD3XYGuphhuqBQksqT+BD27Ie03/Rn75xz/e/VPTw2imT6dxGpfTqRnacws49JDnBjLnTZhY8lxFfMMQE9yvwHrPWeOZzvrmvUUIG2Bfv4eGI4AB5CbHE+cQ0h0WpaGXJCb7bBofY8NmKTBZR3xOBNmP8xZezCKdDc3Wgs31xZIBECM9m+mYTHWulp4VCOWWJXXrmCHXrCA13Q9Zopfyv0+YKxVNzcL6+OSMev/TmZ4/3nVGXIsBKcYndeoEqTAtFqoPrPExJ5VHwNmYjuQVjZMIZZfWaZ8LTIl0QgFpy3xybjsX91OchcajImlW6ilnrbkAIjiNAgxhfRQBYKOwxfmLI5LKeX3wsqt7afgjU35gyyFjfmDNdnOQId3xbDnuc64CwrNI9XJ80p/IjVnLjZGmc+QCWgUyP8HIkIPy/R4oQ6/ENuBHzgcCeTEtsTQilZ3JXqCSHGG+KQYVLm5B0iMXsIpLKmeeSL8BQrlY6w2BpmBrDiB8hWNxvIK7rj+SR4V3w73rvv3VsA2I7ayIDL474K8dOYOGnKeaHJE8D8upUCTkfCSfnG5vMLi7EfNrtjsrLy65Q4Svjsij9MEz+GD1Ix+sPh4LUQ+ETxufrCZSNDpc0FYnk73lAKzxbCMWVBv/oG3bUtqxAsJCAmFXB8lemUjIsUSH2wWG5Ac5K1Ko4nWEgOEnE8CiqFBr7FJzSJYlZA1OGwgasO1QWB4FsZeIyb//wWkz2IU9AscyGU8EgSfPSLSb8GS1LnfFGW4IF7dvhOPlUD6FphyXM/wDM5SBh2fkOAMsk/yV6RU3jknez01e6ZJDnDFwduuayN2c1SHV5YksTut+U3CtCOPuBHzO0eMnpDmgIe2wWTegwMUBBVilQHMDxxcTIrh3wkwJ/IYW/V1T+I7XTeEEpWlXyQxBJl8TSlry/vjfH7j8L4S9wN9SQGhPb6iO9JlYqm6A8xxtmFlLTam5xBjhByDGTMPa2cQ6JWppmWKWQCV7fGJMsb4lKBenN1RZNlbfUSzPcnOmjq49VSyVV75gXaLr30kdhFDHQaybanmU0lDlO1KuyRaLP5twjZQNaYbSzyZtkHJOmtH0s0nn1iGsUFdsq06ZyAg6havMo1kDtvRl5eEuepj2hJfo604MHNJjRxP6ailU7MyNFnkJqRkPnO5B9DbgW0SL7CXi8N0JUr7Hik6ZA8ep7NGAsJtKA+piONOA78FmP9LAyecHqFsvuHWgSWn4e2ASHZHKKafk2AIZX5B8WSO7XWd4dtHv3E2/nD1ML8/u+MQrwj6ZHIOAEPLdhi3HxrUtMEM2tsABObfRA6LgZqCIvc32lNkS5WRpbSseOrLppU2vZAKYy7NOkWFvISnIupheCis9wp5NeiVP7FlVHpvUa0hWp+HFyd4hSDOZstFyfsrQTKpwzzO1j0S4IUDq4ZxdwgLH8xnelk1oRuscQIJXKthYVbcjGS7LzOzK/fhK2Ag6ECZTfktHWge1B3+ia/CSQrrCaZjy6FdLWqX0gutdXEYj4TnTUJyGTTs7ZZSciSYUKvHwaGMPZtc2Ct+wPKbPqvJp5uBV1zy44/X66bFKSPt6dYFnCUCHSlFy/FRuTQQHBoqQsQEuVG4XC6IhOyU0YblZegXEOHELIbLEd4tCVnCqKCq2QIDDQwCB5geAsJZAmC3TgNC1BEHZPNhxUB7nfLhv4p2WUBvvxcS1fSjpQrg3IrtwnC9ve+6D3Atx8UYA3Nr0mbjyCNfpAoMLgURgxCsCSuizLe/XpHbTtn1Ygi8kJ4owWIgeI+7SdGe2K/3MsODE64/JVeWKWnLiGYGE1DHfVUmQnr2Bu91v6+NjQ+40I2xuMsEwY+Rp265HGuzQwJyJIfFoABcvHVAmd4tRAROzNX4z0VtHbGBGKli4g3R2a344lk4dmPw6PU8y30v0WNNpRtwuEKHlE/cCDIGme05obibewg89nZ3QzIGKjaFURvdGPosR+pm0fI/RlsbD9JIQIy25qTiSZyvwMY2SBN/FkIe41+aYfp7Y/KGCuBuV6Nwq00ErWIWkmQlaf7b4cnG9Zn0SAKjBQoQljSUebkisHvV0PAbojYggsT8NXtB+A8ob/EYUwyGTJKYVM15rsVLunQ+zn2U8bd4At1wH/HHGT26uVvo31cKXx/9vtfytWkOhlgSBv23GuFvfRK1AMdZ2lKdzMkdUc+3oPWELk853T0GVZjJ+dt5LDQpZgei0/HGWp/fjbGJVIQODMQtjoJcy124jXNcTiJ8rHJJ9PK9pHxZFoU8Z/NPSnllVuZgwJaQhBjQa4AlC+9aW8kTM7eJ9y6YDPF4WYKZsboseYd2Y9qEoeFIUFair7Sr8sbA2qEYqOk0x16DStLCs3YOn2scbs5Wwlk1T5efLup8bkAGY4FOfTIL/55Djq101dnVIYMuuJup1hr4QlpiC9E5U69XxyOzWqoWnI+1L7WjfgTOADo9av6Utq06DHEZfJA58cTHBtb362lju3I+9SWORXrXIo1rkkQuMlP6vf+Ut7heZTkH46+Tg8b/lnCVLRk0letRwzSdUT75k0QdCP8EFJIlLs6VLW+kK94M+qOlBfTqP0xfzAOzxswIqF0ysOP3dyL0NvscnsW+cUP+POsKa5wQIAVeGCgzbc6P0rf1j/+XAsQ863tZ17KKFtxMVrdVtlH5Tvv+GpbIojVa+wnBCOF10+CZ2ZAfqv28mjRQfR0dVtaz3ll7Xlt5btnrLk6TaZQEmPNeF4eEMKZVt0yjmvgezlqamUywKp1ML8OWr/eO6P0vdQ65tdBAwsMBCLMiTt1isnrdx9trcw/vXPZO/ytV8B0royhoU5f80/iF5zBqvnAJkjwJk9ELchOvpXoqmFzLibs1jR5xMwI25aI5S6Jc6cIZIWdYp+LxFZ3UKpi56V6c8cjlbsNFlrT2rte9q7S8iy8vK5hO3g94Sdo+jeHxkpgUn5qVXrOJUVCLPxLgZPejGEftq4pvykaHav4BnVQkMbDj3qIXlFD/t1HUHy0qxnCg5ZVy6383WPMvmSQQV4aJl/3pcuyOhW7cpf1sv0+/ENE7/s14kuqpE+XcenUMIr0UtDqLWfz4aR8ZvKah6+uby5uLucdjRc/xgqA/d80HvQm+9bbfP8jyJ2u3Lu0t9OOiN7nQQ1W53rls6zGvRssxP2u3VaoXPQUJN5GXtYZHlUVFuBiDvLcxxwjJsbRcU6zT02w7iB+Cq91sJrVO4KH8ceH6UnLax2Rxk/HvQR/E5OvTgYp+etiVxXwxoNi+8xVkxXy6itGSHJHpF4dVpjXV+FwtNMYL/OLBQk5kFRZyXP2RG1vbuckrVUQlx7RUh//49BAl/YX37xSvaSTZvS+3EuviUlBV/4Y1+FOVnSfwSHRJdFsuovd2XdmNjTtt8E2Xf0ug1GRvtEf+Y3B7EfuEVm/bAg9sXPZujow37B8OXfMtw/M/DEyca3RAjEUPThA9FhcPXNzR6Dgv/2f6yZHHQju+WacTajmR28g0X64SARz9bt504DaM1kieaS4nxNk4h8vG7JQ+/Ve3GdaJuEy1IXgFt2S3h2tZkW99APJob+9yCehugv1imceCVkUwU5818vA1R3WVk4+Ce5Mjq9nhJjBWlK+qIcx79vZ16yX2V9y8us3qwcHs7t1S2PnzGAKM4ClQ1X68YRb2It97e9syqqVzVW7IIdns2s1RZxF8mZvyoAvdVhddMFl3qAusGu4Zec0MDoqTuGWzTzWGjgx2jlX5u0FBKV3p9l1/izVr0EpfZtfgk4KC/5aHg8MYWWozvE/gwNJ0S0ppOF14Mt//WiZhG0WTG3z6xwtV4YYufY90RYT2BTNOl6kUKvNGzPrqjo1/EJWkITGPovhMvrS+yiycMB+7QplheVadNc4lLce1qPHXJm0utlC7qnnOvyJgpmOKmMTRAvBElMYSZaU0ae+B6xL1SRbubYdEOfVWxg0Kup+p5Nzvs3qaCvaaCvV0FL9WLFa6ALzvoA9u9rEFGvlV4Jnu1x+x1cgRO1f4X0roFxA==')))
# Created by pyminifier (https://github.com/liftoff/pyminifier)

